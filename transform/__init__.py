from flask import Flask

app = Flask(__name__)

from .views import test_views  # noqa
from .views import main  # noqa


__version__ = "1.0.0"
