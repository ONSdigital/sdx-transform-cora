from flask import Flask
import logging
from structlog import wrap_logger

from . import settings

__version__ = "2.1.0"

logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
logger = wrap_logger(logging.getLogger(__name__))
    
logger.info("Starting Transform Cora", version=__version__)

app = Flask(__name__)

from .views import test_views  # noqa
from .views import main  # noqa
