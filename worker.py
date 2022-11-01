from lib.server import R_CONN

import json
import os

# Envionrment Variabels
REDIS_EXPIRY=int(os.getenv('REDIS_EXPIRY', 30))

def sub_routine():
    sub = R_CONN.pubsub()
    sub.subscribe('clean')
    for msg in sub.listen():
        if isinstance(msg['data'], bytes):
            msg = json.loads(msg['data'].decode('utf8'))
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
                R_CONN.lrem('games:%s:logs' % msg['game_token'])


while __name__ == '__main__':
    while True:
        sub_routine()