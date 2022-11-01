from lib.client.player import Client

import asyncio
import random
import os

# Environment Variables
CLIENT_GAMES=os.getenv('CLIENT_GAMES', 10)

async def main(games_played=0):
    while games_played < CLIENT_GAMES:
        client = Client()
        await client.login()
        await client.join(random.randint(2, 3))
        await client.lobby()
        games_played += 1

asyncio.run(main())