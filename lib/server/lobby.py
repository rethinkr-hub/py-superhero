from functools import wraps
from uuid import uuid4
from lib.server import router, R_CONN, misc

import websockets
import datetime
import asyncio
import logging
import random
import json
import os

# Enivornment Variables
SERVER_SLEEP=float(os.getenv('SERVER_SLEEP', 5))
LOBBY_TIMEOUT=int(os.getenv('LOBBY_TIMEOUT', 5))
LOGGER_MODULE=os.getenv('LOGGER_MODULE', 'default')

# Setup
QUEUE=__name__
logger=logging.getLogger('%s.%s' % (LOGGER_MODULE, QUEUE))

# Errors
class NoOpenGamesError(Exception):
    pass

def validate_user_token(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        logger.debug('Decorator Validating User Token')
        route, ws, msg = args
        if not 'USER_TOKEN' in msg['PAYLOAD']:
            await ws.send(json.dumps({
                'PAYLOAD': {},
                'STATUS': 'MISSING USER TOKEN IN PAYLOAD'
            }))
        else:
            return await f(*args, **kwargs)
    
    return wrapper

def validate_participants(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        logger.debug('Decorator Validating Requested Participants')
        route, ws, msg = args
        if not 'PARTICIPANTS' in msg['PAYLOAD']:
            await ws.send(json.dumps({
                'PAYLOAD': {},
                'STATUS': 'MISSING PARTICIPANTS IN PAYLOAD'
            }))
        else:
            return await f(*args, **kwargs)
    
    return wrapper

def validate_game_token(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        logger.debug('Decorator Validating Game Token')
        route, ws, msg = args
        if not 'GAME_TOKEN' in msg['PAYLOAD']:
            await ws.send(json.dumps({
                'PAYLOAD': {},
                'STATUS': 'MISSING GAME TOKEN IN PAYLOAD'
            }))
        else:
            return await f(*args, **kwargs)
    
    return wrapper

def find_open_games(participants):
    logger.debug('Searching Open Games')
    try:
        open_games = []
        for g in R_CONN.lrange('games:players:%d' % participants, 0, -1):
            if not g is None:
                game_status = R_CONN.get('games:%s:status' % g.decode('utf8'))
                if not game_status is None and game_status.decode('utf8') in ['Initializing', 'Waiting Lobby', 'Time Out']:
                    open_games.append(g.decode('utf8'))
                    
        if len(open_games) == 0:
            raise NoOpenGamesError('No Open Games Available to Join')
    finally:
        return open_games
    

@router.route('/api/v1/game/find')
class JoinRoute:
    
    def create_game(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            logger.debug('Decorator Creating Game')
            route, ws, msg = args
            participants = int(msg['PAYLOAD']['PARTICIPANTS'])
            open_games = find_open_games(participants)
            
            if len(open_games) == 0:
                game_token = str(uuid4())
                R_CONN.rpush('games:players:%d' % participants, game_token)
                R_CONN.zadd('games:participants', {game_token: 0})
                R_CONN.set('games:%s:participants' % game_token, participants)
                R_CONN.set('games:%s:status' % game_token, 'Waiting Lobby')
                R_CONN.set('games:%s:host' % game_token, msg['PAYLOAD']['USER_TOKEN'])
                args[2]['PAYLOAD']['GAME_TOKEN'] = game_token
            
            return await f(*args, **kwargs)
        
        return wrapper
        
    def select_character(self, game_token, user_token):
        logger.debug('Registering Super Hero')
        while True:
            id = random.randint(1, R_CONN.hlen('superheros'))
            if not R_CONN.sismember('games:%s:superheros' % game_token, id):
                hero = json.loads(R_CONN.hget('superheros', id))
                R_CONN.hset('games:%s:superheros:%s' % (game_token, user_token), 'id', id)
                R_CONN.hset('games:%s:superheros:%s' % (game_token, user_token), 'attack', hero['powerstats']['attack'])
                R_CONN.hset('games:%s:superheros:%s' % (game_token, user_token), 'health', hero['powerstats']['health'])
                R_CONN.sadd('games:%s:superheros' % game_token, id)

                return id

    @misc.validate_payload
    @validate_user_token
    @validate_participants
    @create_game
    async def find_game(self, ws, message):
        logger.debug('Finding Available Game to Join')

        try:
            participants = int(message['PAYLOAD']['PARTICIPANTS'])
            if not 'GAME_TOKEN' in message['PAYLOAD']:
                open_games = find_open_games(participants)
                game_token = open_games[random.randint(0, len(open_games) - 1)]
            else:
                game_token = message['PAYLOAD']['GAME_TOKEN']
        
            R_CONN.zincrby('games:participants', 1, game_token)
            R_CONN.sadd('games:%s' % game_token, message['PAYLOAD']['USER_TOKEN'])
            log = json.dumps({
                'PAYLOAD': {
                    'GAME_TOKEN': game_token,
                    'HERO_ID': self.select_character(game_token, message['PAYLOAD']['USER_TOKEN'])
                },
                'STATUS': {
                    'JOINED': 'SUCESS'
                }
            })
            logging.info('Hero Selected', extra={'queue': QUEUE, 'task': log})
            await ws.send(log)
        except (NoOpenGamesError, ValueError):
            logger.error('User: %s | No Available Games to Join - Retrying Search' % message['PAYLOAD']['USER_TOKEN'])
            await self.find_game(ws, message)

    async def handle(self, ws, path):
        try:
            async for message in ws:
                msg = json.loads(message)
                await self.find_game(ws, msg)

        except websockets.exceptions.ConnectionClosedError:
            pass

        await ws.close()

def waiting_lobby(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        route, ws, msg = args
        logger.debug('Decorator Waiting Lobby')
        game_token = msg['PAYLOAD']['GAME_TOKEN']
        R_CONN.set('games:%s:status' % game_token, 'Waiting Lobby')

        return await f(*args, **kwargs)
        
    return wrapper

def validate_participants(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        route, ws, msg = args
        logger.debug('Verifying Participant # Exists')
        game_token = msg['PAYLOAD']['GAME_TOKEN']
        
        if R_CONN.get('games:%s:participants' % game_token) is None:
            R_CONN.set('games:%s:status' % game_token, 'Timed Out')
            log = json.dumps({
                'TIMESTAMP': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'PAYLOAD': {
                    'GAME_TOKEN': game_token
                },
                'STATUS': {
                    'GAME': 'TIMED OUT'
                }
            })
            logger.info('Game Timed Out', extra={'queue': QUEUE, 'task':log})
            return await ws.send(log)

        return await f(*args, **kwargs)
    
    return wrapper

@router.route('/api/v1/game/lobby')
class LobbyRoute:
    
    def get_hero(self, game_token, user_token):
        logger.debug('Pulling Hero Attributes')
        id = R_CONN.hget('games:%s:superheros:%s' % (game_token, user_token), 'id')
        if not id is None:
            return {
                'token': user_token,
                'id': int(R_CONN.hget('games:%s:superheros:%s' % (game_token, user_token), 'id')),
                'attack': int(R_CONN.hget('games:%s:superheros:%s' % (game_token, user_token), 'attack')),
                'health': int(R_CONN.hget('games:%s:superheros:%s' % (game_token, user_token), 'health')),
            }
        
        return {
            'token': user_token,
            'id': None,
            'attack': 0,
            'health': 0
        }
    
    def get_participant_heros(self, game_token, participant_tokens):
        logger.debug('Pull Game\'s Participating Heros')
        heros = {}
        for p in participant_tokens:
            heros[p] = self.get_hero(game_token, p)
        
        return heros
    
    async def health_check(self, game_token):
        logger.debug('Validating Game Health')
        healthy = set()
        participants = [p.decode('utf8') for p in R_CONN.smembers('games:%s' % game_token)]
        for p in participants:
            if int(R_CONN.hget('games:%s:superheros:%s' % (game_token, p), 'health').decode('utf8')) > 0:
                healthy.add(p)

        if len(healthy) == 1:
            R_CONN.set('games:%s:status' % game_token, 'Completed')
        else:
            R_CONN.set('games:%s:status' % game_token, 'In-Progress')
    
    async def clean_game(self, user_token, game_token):
        logger.debug('Clean Game')
        await asyncio.sleep(SERVER_SLEEP * 3)
        log = {'game_token': game_token, 'user_token': user_token}
        logger.info('Cleaning Game Records', extra={'queue': QUEUE, 'task':log})

    async def handle_game_turn(self, ws, user_token, game_token, session_time=0):
        logger.debug('Handling Next Player Turn')
        while R_CONN.get('games:%s:status' % game_token).decode('utf8') != 'Completed':
            await self.health_check(game_token)

            game_status = R_CONN.get('games:%s:status' % game_token)
            logger.debug('Game:%s | Status:%s' % (game_token, game_status))
            if not game_status == 'In-Progress':
                # Potential Break
                player = R_CONN.lindex('games:%s:order' % game_token, 0).decode('utf8')
                player_hero = self.get_hero(game_token, user_token)
                if (
                    R_CONN.get('games:%s:status' % game_token).decode('utf8') != 'Waiting Player' and \
                    player == user_token and \
                    player_hero['health'] > 0
                ):
                    R_CONN.set('games:%s:status' % game_token, 'Waiting Player')
                    log = json.dumps({
                        'PAYLOAD': {
                            'GAME_TOKEN': game_token
                        },
                        'STATUS': {
                            'GAME': 'USER\'S TURN'
                        }
                    })
                    logging.info('Pushing User\'s Turn Notification', extra={'queue': QUEUE, 'task': log})
                    await ws.send(log)
            
            session_time += SERVER_SLEEP
            await asyncio.sleep(SERVER_SLEEP)
        
        log = json.dumps({
            'PAYLOAD': {
                'GAME_TOKEN': game_token
            },
            'STATUS': {
                'GAME': 'COMPLETE'
            }
        })
        logging.info('Game Finished', extra={'queue': QUEUE, 'task': log})
        await ws.send(log)
        await self.clean_game(user_token, game_token)

    @misc.validate_payload
    @validate_user_token
    @validate_game_token
    @validate_participants
    async def wait_players(self, ws, msg, session_time=0):
        logger.debug('Waiting Next Player Action')
        game_token = msg['PAYLOAD']['GAME_TOKEN']
        game_participants = int(R_CONN.get('games:%s:participants' % game_token).decode('utf8'))
        
        while True:
            # Potential Break
            if R_CONN.zmscore('games:participants', [game_token])[0] >= game_participants:
                participants = [p.decode('utf8') for p in R_CONN.smembers('games:%s' % game_token)]
                participants_heros = self.get_participant_heros(game_token, participants)
                R_CONN.set('games:%s:status' % game_token, 'Starting')
                if R_CONN.llen('games:%s:order' % game_token) == 0:
                    for p in sorted(participants):
                        R_CONN.rpush('games:%s:order' % game_token, p)
                
                try:
                    log = json.dumps({
                        'TIMESTAMP': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'PAYLOAD': {
                            'GAME_TOKEN': game_token,
                            'PARTICIPANTS': participants,
                            'PARTICIPANTS_HEROS': participants_heros,
                        },
                        'STATUS': {
                            'GAME': 'START'
                        }
                    })
                    logger.info('Starting Match', extra={'queue': QUEUE, 'task':log})
                    await ws.send(log)

                    break
                except websockets.exceptions.ConnectionClosedError:
                    pass
            elif session_time > LOBBY_TIMEOUT:
                R_CONN.set('games:%s:status' % game_token, 'Timed Out')
                log = json.dumps({
                    'TIMESTAMP': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'PAYLOAD': {
                        'GAME_TOKEN': game_token
                    },
                    'STATUS': {
                        'GAME': 'TIMED OUT'
                    }
                })
                logger.info('Game Timed Out', extra={'queue': QUEUE, 'task':log})
                await ws.send(log)

                return await self.clean_game(msg['PAYLOAD']['USER_TOKEN'], game_token)
            
            session_time += SERVER_SLEEP
            await asyncio.sleep(SERVER_SLEEP)
        
        if R_CONN.get('games:%s:status' % game_token).decode('utf8') == 'Starting':
            R_CONN.set('games:%s:status' % game_token, 'In-Progress')

        user_token = msg['PAYLOAD']['USER_TOKEN']
        await self.handle_game_turn(ws, user_token, game_token)
    
    async def handle(self, ws, path):
        try:
            async for message in ws:
                msg = json.loads(message)
                await self.wait_players(ws, msg)

        except websockets.exceptions.ConnectionClosedError:
            pass

        try:
            await ws.wait_closed()
        finally:
            pass