import os
from nsj_jobs.resources.envconfig import EnvConfig



class ServiceDocumentCMD():
    def __init__(self, dir_instalacao_erp):
        self.dir_instalacao = dir_instalacao_erp
        self.exe_service_document = 'nsjServiceDocumentEngine.exe'
        self.autoexec = 'AUTOEXEC'
        env_config = EnvConfig.instance()
        self.database_host = env_config.database_host
        self.database_name = env_config.database_name
        self.database_port = env_config.database_port
        self.erp_user = env_config.erp_user
        self.erp_password = env_config.erp_password
    
    def executar(self):
        params = [
            self.exe_service_document,
            self.autoexec,
            self.database_host,
            self.database_name,
            self.database_port,
            self.erp_user,
            self.erp_password
        ]
        # TODO log de execução do service document
        os.chdir(self.dir_instalacao)
        os.system(" ".join(params))