import logging
import os
import glob

def log_level(level):
    return {
        'CRITICAL': logging.CRITICAL,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG
    }.get(level, logging.NOTSET)


# Setup
logging.getLogger('asyncio').setLevel(log_level('ERROR'))
logging.getLogger('asyncio.coroutines').setLevel(log_level('ERROR'))
logging.getLogger('websockets.server').setLevel(log_level('ERROR'))
logging.getLogger('websockets.protocol').setLevel(log_level('ERROR'))

modules = glob.glob(os.path.join(os.path.dirname(__file__), "*.py"))
__all__ = [ os.path.basename(f)[:-3] for f in modules if os.path.isfile(f) and not os.path.basename(f)[:-3].startswith('_')]
