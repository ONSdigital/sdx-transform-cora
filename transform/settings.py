import json
import logging
import os

LOGGING_FORMAT = "%(asctime)s|%(levelname)s: sdx-transform-cora: %(message)s"
LOGGING_LEVEL = logging.getLevelName(os.getenv('LOGGING_LEVEL', 'DEBUG'))

SDX_FTP_IMAGES_PATH = "EDC_QImages"
SDX_FTP_DATA_PATH = "EDC_QData"
SDX_FTP_RECEIPT_PATH = "EDC_QReceipts"


if not os.getenv("CF_DEPLOYMENT", False):
    SDX_SEQUENCE_URL = os.getenv("SDX_SEQUENCE_URL", "")
    FTP_PATH = os.getenv("FTP_PATH", "\\\\NP3RVWAPXX370\\SDX_preprod\\")

