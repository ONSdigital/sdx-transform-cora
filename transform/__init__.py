from flask import Flask

app = Flask(__name__)

from .views import main  # noqa

__version__ = "1.3.0"
