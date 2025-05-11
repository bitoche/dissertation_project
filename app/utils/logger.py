import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(logging_config):
    logger = logging.getLogger('financial_calculator')
    log_level = logging_config.get('level', 'INFO').upper()
    logger.setLevel(getattr(logging, log_level))
    
    log_file = logging_config.get('file', '/app/logs/calculator.log')
    handler = RotatingFileHandler(log_file, maxBytes=1000000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)