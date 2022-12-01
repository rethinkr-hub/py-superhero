from lib.client.player import Client
from lib.utils import loggers

import websockets
import importlib
import asyncio
import logging
import random
import os

# Environment Variables
CLIENT_GAMES=int(os.getenv('CLIENT_GAMES', 10))
LOGGER_MODULE=os.getenv('LOGGER_MODULE', 'default')

async def main(games_played=0):
    logger_module = importlib.import_module('lib.utils.loggers.%s' % LOGGER_MODULE)
    
    # Setup
    QUEUE='client.%s' % __name__
    logger=logging.getLogger('%s.%s' % (LOGGER_MODULE, QUEUE))
    
    while games_played < CLIENT_GAMES:
        logger.info('Starting Game %d' % (games_played + 1), extra={'queue': QUEUE})
        client = Client()
        try:
            await client.login()
            await client.join(random.randint(2, 3))
            await client.lobby()
            games_played += 1
        except (websockets.exceptions.InvalidStatusCode, OSError):
            await asyncio.sleep(5)
            pass

asyncio.run(main())