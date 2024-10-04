import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name=__name__):
    # Determine the environment; default to 'production' if not set
    env = os.getenv('ENV', 'production').lower()

    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set the lowest level to capture all messages

    # Avoid adding multiple handlers if the logger is already configured
    if not logger.handlers:
        # Create handlers based on environment
        if env == 'development':
            # Console handler for development
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        elif env == 'testing':
            # File handler for testing
            file_handler = RotatingFileHandler('testing.log', maxBytes=10**6, backupCount=3)
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        elif env == 'production':
            # File handler with higher level for production
            file_handler = RotatingFileHandler('production.log', maxBytes=10**7, backupCount=5)
            file_handler.setLevel(logging.WARNING)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        else:
            # Default to console handler if environment is unknown
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # Optionally, add a handler to capture ERROR and above to a separate file
        error_handler = RotatingFileHandler('errors.log', maxBytes=10**6, backupCount=3)
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        error_handler.setFormatter(error_formatter)
        logger.addHandler(error_handler)

    return logger
