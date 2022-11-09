from lib.server import R_CONN

import json
import os

# Envionrment Variabels
WORKER_CHANNEL=os.getenv('WORKER_CHANNEL', 'CLEAN').upper()
REDIS_EXPIRY=int(os.getenv('REDIS_EXPIRY', 30))

def redis_publisher(message):
    R_CONN.publish(WORKER_CHANNEL, json.dumps(message))

class Redis_Subscriber:

    @property
    def callback_function(self):
        return
    
    @callback_function.setter
    def callback_function(self, callback_function):
        self._callback_function = callback_function
    
    def run(self):
        sub = R_CONN.pubsub()
        sub.subscribe(WORKER_CHANNEL)
        for msg in sub.listen():
            if isinstance(msg['data'], bytes):
                msg = json.loads(msg['data'].decode('utf8'))
                self._callback_function(msg)
    
    def stop(self):
        return