from functools import wraps
from uuid import uuid4
from lib.server import router, R_CONN, misc
from lib.server.lobby import LobbyRoute, validate_game_token, validate_user_token

import websockets
import datetime
import logging
import json
import os

# Environment Variables
BASE_LOGGER=os.getenv('BASE_LOGGER', 'base')

# Setup
QUEUE=__name__
logger=logging.getLogger('%s.%s' % (BASE_LOGGER, QUEUE))

def validate_action(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        logger.debug('Decorator Validating Action Message')
        route, ws, msg = args
        if not 'ENEMY_TOKEN' in msg['PAYLOAD']:
            await ws.send(json.dumps({
                'PAYLOAD': {},
                'STATUS': 'MISSING ENEMY TOKEN IN PAYLOAD'
            }))
        if not 'ACTION' in msg['PAYLOAD']:
            await ws.send(json.dumps({
                'PAYLOAD': {},
                'STATUS': 'MISSING ACTION IN PAYLOAD'
            }))
        else:
            return await f(*args, **kwargs)
    
    return wrapper

@router.route('/api/v1/game/action')
class GameActionRoute(LobbyRoute):
    
    def attack(self, game_token, player_hero, enemy_hero):
        logger.debug('Registering Attack')
        combat = {
            'enemy_health_prior': enemy_hero['health'],
            'user_attack_damage': player_hero['attack'],
            'enemy_health_post': max(enemy_hero['health'] - player_hero['attack'], 0)
        }

        R_CONN.hset('games:%s:superheros:%s' % (game_token, enemy_hero['token']), 'health', combat['enemy_health_post'])

        return combat

    @misc.validate_payload
    @validate_user_token
    @validate_game_token
    @validate_action
    async def action(self, ws, msg):
        logger.debug('Processing Action')
        if msg['PAYLOAD']['ENEMY_TOKEN']:
            player_hero = self.get_hero(msg['PAYLOAD']['GAME_TOKEN'], msg['PAYLOAD']['USER_TOKEN'])
            enemy_hero = self.get_hero(msg['PAYLOAD']['GAME_TOKEN'], msg['PAYLOAD']['ENEMY_TOKEN'])
            combat = self.attack(msg['PAYLOAD']['GAME_TOKEN'], player_hero, enemy_hero)

            log = json.dumps({
                'TIMESTAMP': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'PAYLOAD': {
                    'GAME_TOKEN': msg['PAYLOAD']['GAME_TOKEN'],
                    'USER_TOKEN': msg['PAYLOAD']['USER_TOKEN']
                },
                'STATUS': {
                    'ACTION': 'ATTACK',
                    'DETAILS': {
                        'ENEMY_TOKEN': msg['PAYLOAD']['ENEMY_TOKEN'],
                        'ENEMY_DAMAGE': combat['user_attack_damage'],
                        'ENEMY_HEALTH_PRIOR': combat['enemy_health_prior'],
                        'ENEMY_HEALTH_POST': combat['enemy_health_post']
                    }
                }
            })

            logger.info('Attack Completed', extra={'queue': QUEUE, 'task':log})
            R_CONN.rpush('games:%s:logs' % msg['PAYLOAD']['GAME_TOKEN'], log)
            if combat['enemy_health_post'] == 0:
                R_CONN.lrem('games:%s:order' % msg['PAYLOAD']['GAME_TOKEN'], 1, msg['PAYLOAD']['ENEMY_TOKEN'])

            next_player = R_CONN.lmove(
                'games:%s:order' % msg['PAYLOAD']['GAME_TOKEN'], 
                'games:%s:order' % msg['PAYLOAD']['GAME_TOKEN'], 
                'LEFT', 'RIGHT')
        else:
            R_CONN.set('games:%s:status' % msg['PAYLOAD']['GAME_TOKEN'], 'Completed')
            log = json.dumps({
                'TIMESTAMP': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'PAYLOAD': {
                    'GAME_TOKEN': msg['PAYLOAD']['GAME_TOKEN'],
                    'USER_TOKEN': msg['PAYLOAD']['USER_TOKEN']
                },
                'STATUS': {
                    'ACTION': 'NA',
                    'DETAILS': {
                        'ENEMY_TOKEN': msg['PAYLOAD']['ENEMY_TOKEN'],
                        'ENEMY_STATUS': 'DEAD'
                    }
                }
            })
            logger.error('Attacked Dead Enemy', extra={'queue': QUEUE, 'task':log})
        
        await ws.send(log)
    
    async def handle(self, ws, path):
        try:
            async for message in ws:
                msg = json.loads(message)
                await self.action(ws, msg)

        except websockets.exceptions.ConnectionClosedError:
            pass

        await ws.close()
        
@router.route('/api/v1/game/hero')
class GameHeroRoute(LobbyRoute):

    @misc.validate_payload
    @validate_user_token
    @validate_game_token
    async def hero(self, ws, msg):
        # Potential Breaking Point
        logger.debug('Assigning Hero')
        hero = self.get_hero(msg['PAYLOAD']['GAME_TOKEN'], msg['PAYLOAD']['USER_TOKEN'])
        await ws.send(json.dumps({
            'PAYLOAD': {
                'GAME_TOKEN': msg['PAYLOAD']['GAME_TOKEN'],
                'USER_TOKEN': msg['PAYLOAD']['USER_TOKEN'],
                'HERO': hero
            },
            'STATUS': {
                'GAME': 'HERO SPEC'
            }
        }))
    
    async def handle(self, ws, path):
        try:
            async for message in ws:
                msg = json.loads(message)
                await self.hero(ws, msg)

        except websockets.exceptions.ConnectionClosedError:
            pass

        await ws.close()