from functools import wraps
import json

def validate_payload(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        route, ws, msg = args
        if not 'PAYLOAD' in msg:
            await ws.send(json.dumps({
                'PAYLOAD': {},
                'STATUS': 'MISSING PAYLOAD IN MESSAGE'
            }))
        else:
            return await f(*args, **kwargs)
    
    return wrapper