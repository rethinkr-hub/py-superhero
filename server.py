#!/usr/bin/env python

# Fork of websockets Quick Start
# https://websockets.readthedocs.io/en/stable/intro/quickstart.html

# Websocket History & Areas of Improvement
# https://ably.com/topic/websockets

from lib.server import router
from lib.server.login import LoginRoute
from lib.server.lobby import JoinRoute, LobbyRoute
from lib.server.game import GameActionRoute, GameHeroRoute
from lib.utils.loggers import *

import websockets
import asyncio
import logging
import os

# Environment Variables
WEBSOCKET_HOST=os.getenv('WEBSOCKET_HOST', 'localhost')
WEBSOCKET_PORT=int(os.getenv('WEBSOCKET_PORT', '5678'))
BASE_LOGGER=os.getenv('BASE_LOGGER', 'base')

# Setup
QUEUE='server.%s' % __name__
logger=logging.getLogger('%s.%s' % (BASE_LOGGER, QUEUE))

async def main():
    logger.info('Starting Web Socket Server', extra={'queue': QUEUE})
    async with websockets.serve(router, WEBSOCKET_HOST, WEBSOCKET_PORT):
        logger.info('Listening on %s:%d' % (WEBSOCKET_HOST, WEBSOCKET_PORT), extra={'queue': QUEUE})
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())