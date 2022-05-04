import os
import logging
import sys
import time
import json

from flask import Flask
from google.cloud import secretmanager_v1 as secretmanager

# Lendo variáveis de ambiente
APP_NAME = os.environ['APP_NAME']
ENV = os.getenv('ENV', 'prod')
DEBUG = bool(os.getenv('DEBUG', 'False'))

# Reading secrets
if ENV == 'prod':
    EXTERNAL_SECRETS = os.environ['EXTERNAL_SECRETS']
    secret_client = secretmanager.SecretManagerServiceClient()
    external_secrets = json.loads(secret_client.access_secret_version(
        name=EXTERNAL_SECRETS).payload.data.decode('UTF-8'))

    NEXUS_USER = external_secrets["nexus"]["user"]
    NEXUS_PASSWORD = external_secrets["nexus"]["password"]
    DOCKER_HUB_USER = external_secrets["docker_hub"]["user"]
    DOCKER_HUB_PASSWORD = external_secrets["docker_hub"]["password"]
else:
    NEXUS_USER = os.environ["NEXUS_USER"]
    NEXUS_PASSWORD = os.environ["NEXUS_PASSWORD"]
    DOCKER_HUB_USER = os.environ["DOCKER_HUB_USER"]
    DOCKER_HUB_PASSWORD = os.environ["DOCKER_HUB_PASSWORD"]

# Configurando o logger
logger = logging.getLogger(APP_NAME)
if DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)

console_format = logging.Formatter(
    '%(name)s - %(levelname)s - %(message)s')
file_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_format)

logger.addHandler(console_handler)


def log_time(msg: str):
    """Decorator para monitoria de performance de métodos (via log)."""

    def decorator(function):
        def wrapper(*arg, **kwargs):
            t = time.time()
            res = function(*arg, **kwargs)
            logger.info(f'----- {str(time.time()-t)} seconds --- {msg}')
            return res

        return wrapper

    return decorator


# Configurando o Flask
flask_app = Flask('app')
