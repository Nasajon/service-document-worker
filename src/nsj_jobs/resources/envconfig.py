import os
import pathlib
import socket
import uuid


class EnvConfig:
    DIR_EXECUCAO = "nsj_jobs"

    _instance = None

    def __init__(self):
        self.database_host = os.getenv("database_host", "localhost")
        self.database_name = os.getenv("database_name", "nasajon")
        self.database_user = os.getenv("database_user", "postgres")
        self.database_password = os.getenv("database_password", "postgres")
        self.database_port = os.getenv("database_port", "5432")
        self.dir_execucao = self._trata_diretorio_execucao()
        self.log_path = self.dir_execucao / "logs"
        self.log_level = os.getenv("log_level", "DEBUG")
        self.id_execucao = uuid.uuid4()
        self.erp_user = os.getenv("erp_user", "MASTER")
        self.erp_password = os.getenv("erp_password", "")
        self.maximo_tentativas = os.getenv("maximo_tentativas", "24")

    @staticmethod
    def instance():
        if (EnvConfig._instance == None):
            EnvConfig._instance = EnvConfig()

        return EnvConfig._instance

    def _trata_diretorio_execucao(self):
        # Recupera diretório de usuário:
        user_home = pathlib.Path.home()

        # Monta path do diretório de configurações:
        dir_job_manager = user_home / EnvConfig.DIR_EXECUCAO

        # Criando o diretório do JobManager, se necessário:
        if not os.path.exists(dir_job_manager):
            os.makedirs(dir_job_manager)

        return dir_job_manager
