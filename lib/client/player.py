#!/usr/bin/env python

import websockets
import asyncio
import logging
import random
import json
import sys
import os

# Enviornment Variables
WEBSOCKET_HOST=os.getenv('WEBSOCKET_HOST', 'localhost')
WEBSOCKET_PORT=int(os.getenv('WEBSOCKET_PORT', '5678'))
CLIENT_SLEEP=float(os.getenv('CLIENT_SLEEP', 1))

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

class Client:
    USER_TOKEN=None
    GAME_TOKEN=None
    PARTICIPANTS=None
    PARTICIPANTS_HEROS=None

    @property
    def participants(self):
        return self.PARTICIPANTS
    
    @participants.setter
    def participants(self, participants):
        self.PARTICIPANTS = [p for p in participants if p != self.USER_TOKEN]
    
    @property
    def participants_heros(self):
        return self.PARTICIPANTS_HEROS
    
    @participants_heros.setter
    def participants_heros(self, participants_heros):
        self.PARTICIPANTS_HEROS = [participants_heros[p] for p in participants_heros.keys() if p != self.USER_TOKEN]

    async def login(self):
        try:
            USER = 'USER%03d' % random.randint(0,999)
            while True:
                async with websockets.connect('ws://%s:%d/api/v1/login' % (WEBSOCKET_HOST, WEBSOCKET_PORT)) as websocket:
                    await websocket.send(json.dumps({'PAYLOAD': {'USER': USER}}))
                    message = json.loads(await websocket.recv())
                    logging.info(message)

                    if 'PAYLOAD' in message and 'USER_TOKEN' in message['PAYLOAD']:
                        self.USER_TOKEN = message['PAYLOAD']['USER_TOKEN']
                        break
                    else:
                        await asyncio.sleep(CLIENT_SLEEP)

        except websockets.exceptions.ConnectionClosedError:
            pass

    async def join(self, participants):
        try:
            async with websockets.connect('ws://%s:%d/api/v1/game/find' % (WEBSOCKET_HOST, WEBSOCKET_PORT)) as websocket:
                await websocket.send(json.dumps({'PAYLOAD': {'USER_TOKEN': self.USER_TOKEN, 'PARTICIPANTS': participants}}))
                while True:
                    message = json.loads(await websocket.recv())
                    logging.info(message)

                    if 'PAYLOAD' in message and 'GAME_TOKEN' in message['PAYLOAD']:
                        self.GAME_TOKEN = message['PAYLOAD']['GAME_TOKEN']
                        break

        except websockets.exceptions.ConnectionClosedError:
            pass
    
    async def lobby(self):
        try:
            async with websockets.connect('ws://%s:%d/api/v1/game/lobby' % (WEBSOCKET_HOST, WEBSOCKET_PORT)) as websocket:
                await websocket.send(json.dumps({'PAYLOAD': {'GAME_TOKEN': self.GAME_TOKEN, 'USER_TOKEN': self.USER_TOKEN}}))
                while True:
                    message = json.loads(await websocket.recv())
                    logging.info(message)

                    if 'STATUS' in message and 'GAME' in message['STATUS'] and message['STATUS']['GAME'] == 'START':
                        if 'PAYLOAD' in message and set(['PARTICIPANTS', 'PARTICIPANTS_HEROS']) <= set(message['PAYLOAD'].keys()):
                            self.participants = message['PAYLOAD']['PARTICIPANTS']
                            self.participants_heros = message['PAYLOAD']['PARTICIPANTS_HEROS']
                    
                    if 'STATUS' in message and 'GAME' in message['STATUS'] and message['STATUS']['GAME'] == 'USER\'S TURN':
                        await self.action()
                    
                    if 'STATUS' in message and 'GAME' in message['STATUS'] and message['STATUS']['GAME'] in ['COMPLETE', 'TIMED OUT']:
                        break

                    if 'STATUS' in message and 'DETAILS' in message['STATUS'] and 'ENEMY_STATUS' in message['STATUS']['DETAILS'] and \
                        message['STATUS']['DETAILS']['ENEMY_STATUS'] == 'DEAD':
                        break


        except websockets.exceptions.ConnectionClosedError as exc:
            pass
    
    async def select_oponent(self):
        try:
            async with websockets.connect('ws://%s:%d/api/v1/game/hero' % (WEBSOCKET_HOST, WEBSOCKET_PORT)) as websocket:
                participant_heros = {}
                for p in self.participants:
                    await websocket.send(json.dumps({'PAYLOAD': {'GAME_TOKEN': self.GAME_TOKEN, 'USER_TOKEN': p}}))
                    msg = json.loads(await websocket.recv())
                    participant_heros[msg['PAYLOAD']['HERO']['token']] = msg['PAYLOAD']['HERO']
                

        except websockets.exceptions.ConnectionClosedError:
            pass

        self.participants_heros = participant_heros
        healthy_participants = [p['token'] for p in self.participants_heros if p['token'] and p['health'] > 0]
        if len(healthy_participants) > 0:
            return healthy_participants[random.randint(0, len(healthy_participants) - 1)]
        
        return None

    async def action(self):
        try:
            opponent_token = await self.select_oponent()
            async with websockets.connect('ws://%s:%d/api/v1/game/action' % (WEBSOCKET_HOST, WEBSOCKET_PORT)) as websocket:
                await websocket.send(json.dumps({
                    'PAYLOAD': {
                        'GAME_TOKEN': self.GAME_TOKEN, 
                        'USER_TOKEN': self.USER_TOKEN, 
                        'ENEMY_TOKEN': opponent_token,
                        'ACTION': 'ATTACK'
                    }
                }))
                
                message = json.loads(await websocket.recv())
                logging.info(message)


        except websockets.exceptions.ConnectionClosedError:
            pass