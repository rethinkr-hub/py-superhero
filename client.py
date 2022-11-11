from lib.client.player import Client
from lib.utils.loggers import *

import websockets
import asyncio
import logging
import random
import os

# Environment Variables
CLIENT_GAMES=os.getenv('CLIENT_GAMES', 10)
BASE_LOGGER=os.getenv('BASE_LOGGER', 'base')

# Setup
QUEUE='client.%s' % __name__
logger=logging.getLogger('%s.%s' % (BASE_LOGGER, QUEUE))

async def main(games_played=0):
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