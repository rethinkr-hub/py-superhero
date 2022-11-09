from lib.pubsub.redis import redis_publisher as publish
from lib.server import R_CONN

import logging
import json
import sys
import os

# Environment Variables
REDIS_EXPIRY=int(os.getenv('REDIS_EXPIRY', 30))

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def clean_routine(msg):
    if isinstance(msg, bytes):
        msg = json.loads(msg.decode('utf8'))
    
    logging.info('Cleaning Game: %s - User: %s' % (msg['game_token'], msg['user_token']))
    R_CONN.expire('games:%s:superheros:%s' % (msg['game_token'], msg['user_token']), REDIS_EXPIRY)
    R_CONN.expire('games:%s:superheros:%s' % (msg['game_token'], msg['user_token']), REDIS_EXPIRY)
    R_CONN.expire('games:%s:superheros:%s' % (msg['game_token'], msg['user_token']), REDIS_EXPIRY)
    host = R_CONN.get('games:%s:host' % msg['game_token'])
    if host and host.decode('utf8') == msg['user_token']:
        participants = int(R_CONN.get('games:%s:participants' % msg['game_token']))
        R_CONN.expire('games:%s:order' % msg['game_token'], REDIS_EXPIRY)
        R_CONN.expire('games:%s:status' % msg['game_token'], REDIS_EXPIRY)
        R_CONN.expire('games:%s:participants' % msg['game_token'], REDIS_EXPIRY)
        R_CONN.expire('games:%s:host' % msg['game_token'], REDIS_EXPIRY)
                
        R_CONN.zrem('games:participants', msg['game_token'])
        R_CONN.lrem('games:participants:%d' % participants, 1, msg['game_token'])
        R_CONN.delete('games:%s:logs' % msg['game_token']) 