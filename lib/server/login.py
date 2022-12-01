from functools import wraps
from uuid import uuid4
from lib.server import router, R_CONN, misc

import websockets
import logging
import json
import os

# Environment Variables
LOGGER_MODULE=os.getenv('LOGGER_MODULE', 'default')

# Setup
QUEUE=__name__
logger=logging.getLogger('%s.%s' % (LOGGER_MODULE, QUEUE))

@router.route('/api/v1/login')
class LoginRoute:
    def validate_superheros_exist(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            logger.debug('Decorator Validating Super Hero Exists')
            route, ws, msg = args
            if R_CONN.hlen('superheros') <= 0:
                await ws.send(json.dumps({
                    'PAYLOAD': {},
                    'STATUS': 'LIST OF SUPERHEROS NOT AVAILABLE'
                }))
            else:
                return await f(*args, **kwargs)
        
        return wrapper

    def validate_login(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            logger.debug('Decorator Validating User Login')
            route, ws, msg = args
            if not 'USER' in msg['PAYLOAD']:
                await ws.send(json.dumps({
                    'PAYLOAD': {},
                    'STATUS': 'MISSING USER IN PAYLOAD'
                }))
            else:
                return await f(*args, **kwargs)
    
        return wrapper

    def create_user(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            logger.debug('Decorator Creating User')
            route, ws, msg = args
            if not R_CONN.hexists('users', msg['PAYLOAD']['USER']):
                R_CONN.hset('users', msg['PAYLOAD']['USER'], str(uuid4()))
                await ws.send(json.dumps({
                    'PAYLOAD': {},
                    'STATUS': 'USER CREATED'
                }))
            
            return await f(*args, **kwargs)
        
        return wrapper

    @misc.validate_payload
    @validate_login
    @validate_superheros_exist
    @create_user
    async def login(self, ws, message):
        logger.debug('Processing Login')
        user_token = R_CONN.hget('users', message['PAYLOAD']['USER']).decode('utf8')
        await ws.send(json.dumps({
            'PAYLOAD': {
                'USER_TOKEN': user_token,
            }
        }))

    async def handle(self, ws, path):
        try:
            async for message in ws:
                msg = json.loads(message)
                await self.login(ws, msg)

        except websockets.exceptions.ConnectionClosedError:
            pass

        await ws.close()