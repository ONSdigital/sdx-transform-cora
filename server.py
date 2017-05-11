from transform import __version__
from transform import app, settings
import logging
import os
import sys
import logger


def check_globals(module):
    g = {k: v for k, v in vars(module).items() if not k.startswith("_") and k.isupper()}
    return all(g.values())


if __name__ == '__main__':
    # Startup
    logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
    logging.info("Starting server: version='{}'".format(__version__))
    check_default_env_vars()
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
