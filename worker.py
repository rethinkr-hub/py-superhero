from lib.pubsub import clean_routine
from lib.pubsub.redis import Redis_Subscriber
from lib.utils import loggers

import importlib
import logging
import os

# Environment Variables
LOGGER_MODULE=os.getenv('LOGGER_MODULE', 'default')

subscriber = Redis_Subscriber()
subscriber.callback_function = clean_routine

if __name__ == '__main__':
    logger_module = importlib.import_module('lib.utils.loggers.%s' % LOGGER_MODULE)

    # Setup
    QUEUE='worker.%s' % __name__
    logger=logging.getLogger('%s.%s' % (LOGGER_MODULE, QUEUE))

    while True:
        try:
            logger.info('Starting Redis Worker')
            subscriber.run()
        except KeyboardInterrupt:
            logger.info('Closing Redis Worker')
            subscriber.stop()
