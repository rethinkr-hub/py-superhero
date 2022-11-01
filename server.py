#!/usr/bin/env python

# Fork of websockets Quick Start
# https://websockets.readthedocs.io/en/stable/intro/quickstart.html

# Websocket History & Areas of Improvement
# https://ably.com/topic/websockets

from lib.server import router
from lib.server.login import LoginRoute
from lib.server.lobby import JoinRoute, LobbyRoute
from lib.server.game import GameActionRoute, GameHeroRoute
import websockets
import asyncio
import logging
import sys
import os

# Enviornment Variables
WEBSOCKET_HOST=os.getenv('WEBSOCKET_HOST', 'localhost')
WEBSOCKET_PORT=int(os.getenv('WEBSOCKET_PORT', '5678'))

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

async def main():
    logging.info('Starting Web Socket Server')
    async with websockets.serve(router, WEBSOCKET_HOST, WEBSOCKET_PORT):
        logging.info('Listending on %s:%d' % (WEBSOCKET_HOST, WEBSOCKET_PORT))
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())