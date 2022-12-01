from lib.utils.loggers.default import base_handler
from lib.utils.loggers import log_level
from lib.pubsub.redis import redis_publisher

import datetime
import logging
import os

# Environment Variables
LOG_LEVEL=os.getenv('LOG_LEVEL', 'INFO')

class Redis_Handler(logging.StreamHandler):
    """SQL Stream Handler

    Stream log messages to SQL Database.
    """
        
    def emit(self, record):
        """Record Emit

        Format log record and commit to Database.

        Args:
            record: logging record
        """
        if hasattr(record, 'queue') and hasattr(record, 'task'):
            ts = datetime.datetime.fromtimestamp(record.created)
            redis_publisher(record.queue, {
                'level': record.levelname,
                'timestamp': ts.isoformat(),
                'name': record.name,
                'log_message': record.msg,
                'task': record.task
            })
        elif hasattr(record, 'queue'):
            ts = datetime.datetime.fromtimestamp(record.created)
            redis_publisher(record.queue, {
                'level': record.levelname,
                'timestamp': ts.isoformat(),
                'name': record.name,
                'log_message': record.msg
            })

logger = logging.getLogger('redis')
logger.setLevel(log_level('DEBUG'))

redis_handler = Redis_Handler()
redis_handler.setLevel(log_level(LOG_LEVEL))

redis_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
redis_handler.setFormatter(redis_formatter)

logger.addHandler(base_handler)
logger.addHandler(redis_handler)
logger.propagate = False