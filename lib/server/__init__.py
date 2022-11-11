import websockets_routes
import redis
import os

# Enviornment Variables
REDIS_HOST=os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT=int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB=os.getenv('REDIS_DB', 0)

R_POOL = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
R_CONN = redis.Redis(connection_pool=R_POOL, decode_responses=True)

router = websockets_routes.Router()