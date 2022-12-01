from lib.utils.loggers import log_level

import logging
import os

# Environment Variables
LOG_LEVEL=os.getenv('LOG_LEVEL', 'INFO')

logger = logging.getLogger('default')
logger.setLevel(log_level('DEBUG'))

base_handler = logging.StreamHandler()
base_handler.setLevel(log_level(LOG_LEVEL))

base_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
base_handler.setFormatter(base_formatter)

logger.addHandler(base_handler)
logger.propagate = False