import importlib
import requests
import logging
import redis
import json
import sys
import os

# Environmnet Variables
API_TOKEN=os.getenv('API_TOKEN', None)
REDIS_HOST=os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT=int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB=os.getenv('REDIS_DB', 0)
LOGGER_MODULE=os.getenv('LOGGER_MODULE', 'default')

def pull_data(i=1):
    assert(not API_TOKEN is None)
    logger.info('Pulling Super Hero Data', extra={'queue': QUEUE})

    DATA=[]
    while True:
        logger.info('Pulling Hero ID:%d' % i, extra={'queue': QUEUE})
        rs = requests.get('https://www.superheroapi.com/api/%s/%d' % (API_TOKEN, i))
        content = json.loads(rs.text)
        if 'error' in content and content['error'] == 'invalid id':
            break
        
        DATA.append(content)
        i+=1

    with open('superhero.json', 'w') as f:
        logger.info('Writing Data to File', extra={'queue': QUEUE})
        json.dump(DATA, f)

def clean_powerstats(hero):
    if 'power' in hero['powerstats']:
        hero['powerstats']['power'] = int(hero['powerstats']['power']) if not hero['powerstats']['power'] in ['null', '0'] else 1
        
    if 'strength' in hero['powerstats']:
        hero['powerstats']['strength'] = int(hero['powerstats']['strength']) if not hero['powerstats']['strength'] in ['null', '0'] else 1
        
    if 'combat' in hero['powerstats']:
        hero['powerstats']['combat'] = int(hero['powerstats']['combat']) if not hero['powerstats']['combat'] in ['null', '0'] else 1
        
    if 'intelligence' in hero['powerstats']:
        hero['powerstats']['intelligence'] = int(hero['powerstats']['intelligence']) if not hero['powerstats']['intelligence'] in ['null', '0'] else 1
        
    if 'durability' in hero['powerstats']:
        hero['powerstats']['durability'] = int(hero['powerstats']['durability']) if not hero['powerstats']['durability'] in ['null', '0'] else 1
    
    if 'speed' in hero['powerstats']:
        hero['powerstats']['speed'] = int(hero['powerstats']['speed']) if not hero['powerstats']['speed'] in ['null', '0'] else 1
    
    hero['powerstats']['health'] = int(hero['powerstats']['intelligence']) * int(hero['powerstats']['strength']) * int(hero['powerstats']['durability']) * 10
    hero['powerstats']['attack'] = int(hero['powerstats']['speed']) * int(hero['powerstats']['power']) * int(hero['powerstats']['combat'])
    return hero

def write_data():
    R_POOL = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    R_CONN = redis.Redis(connection_pool=R_POOL)

    R_CONN.delete('superheros')
    logger.info('Writing Super Hero Data', extra={'queue': QUEUE})
    with open('superhero.json', 'r') as f:
        DATA = json.load(f)
        for d in DATA:
            d = clean_powerstats(d)
            response = d.pop('response')
            id = d.pop('id')
            R_CONN.hset('superheros', key=id, value=json.dumps(d))

if __name__ == '__main__':
    logger_module = importlib.import_module('lib.utils.loggers', LOGGER_MODULE)
    
    # Setup
    QUEUE='client.%s' % __name__
    logger=logging.getLogger('%s.%s' % (LOGGER_MODULE, QUEUE))
    if len(sys.argv) > 1 and sys.argv[1].upper() == 'PULL':
        pull_data()

    write_data()