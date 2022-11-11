from lib.pubsub import clean_routine
from lib.pubsub.redis import Redis_Subscriber
from lib.utils.loggers import *

import logging
import os

# Environment Variables
BASE_LOGGER=os.getenv('BASE_LOGGER', 'base')

# Setup
QUEUE='worker.%s' % __name__
logger=logging.getLogger('%s.%s' % (BASE_LOGGER, QUEUE))

subscriber = Redis_Subscriber()
subscriber.callback_function = clean_routine

if __name__ == '__main__':
    while True:
        try:
            logger.info('Starting Redis Worker')
            subscriber.run()
        except KeyboardInterrupt:
            logger.info('Closing Redis Worker')
            subscriber.stop()
