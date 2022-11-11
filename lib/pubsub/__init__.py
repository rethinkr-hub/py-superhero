from lib.server import R_CONN

import logging
import json
import os

# Environment Variables
REDIS_EXPIRY=int(os.getenv('REDIS_EXPIRY', 30))
BASE_LOGGER=os.getenv('BASE_LOGGER', 'base')

# Setup
QUEUE=__name__
logger=logging.getLogger('%s.%s' % (BASE_LOGGER, QUEUE))

def clean_routine(msg):
    if isinstance(msg, bytes):
        msg = json.loads(msg.decode('utf8'))
    elif isinstance(msg, str):
        msg = json.loads(msg)
    
    if msg['log_message'] == 'Cleaning Game Records':
        logger.info('Cleaning Game: %s - User: %s' % (msg['task']['game_token'], msg['task']['user_token']))
        R_CONN.expire('games:%s:superheros:%s' % (msg['task']['game_token'], msg['task']['user_token']), REDIS_EXPIRY)
        R_CONN.expire('games:%s:superheros:%s' % (msg['task']['game_token'], msg['task']['user_token']), REDIS_EXPIRY)
        R_CONN.expire('games:%s:superheros:%s' % (msg['task']['game_token'], msg['task']['user_token']), REDIS_EXPIRY)
        host = R_CONN.get('games:%s:host' % msg['task']['game_token'])
        if host and host.decode('utf8') == msg['task']['user_token']:
            participants = int(R_CONN.get('games:%s:participants' % msg['task']['game_token']))
            R_CONN.expire('games:%s:order' % msg['task']['game_token'], REDIS_EXPIRY)
            R_CONN.expire('games:%s:status' % msg['task']['game_token'], REDIS_EXPIRY)
            R_CONN.expire('games:%s:participants' % msg['task']['game_token'], REDIS_EXPIRY)
            R_CONN.expire('games:%s:host' % msg['task']['game_token'], REDIS_EXPIRY)
                
            R_CONN.zrem('games:participants', msg['task']['game_token'])
            R_CONN.lrem('games:participants:%d' % participants, 1, msg['task']['game_token'])
            R_CONN.delete('games:%s:logs' % msg['task']['game_token'])