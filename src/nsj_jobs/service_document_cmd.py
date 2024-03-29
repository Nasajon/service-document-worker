import os




class ServiceDocumentCMD():
    def __init__(self, dir_instalacao_erp, entrada, parametro_execucao = '' ):
        self.dir_instalacao = dir_instalacao_erp
        self.exe_service_document = 'nsjServiceDocumentEngine.exe'
        self.autoexec = 'AUTOEXEC'
        if entrada['env'] == 'docker':
            from nsj_jobs.resources.envconfig import EnvConfig
            env_config = EnvConfig.instance()
            self.erp_user = env_config.erp_user
            self.erp_password = env_config.erp_password
        elif entrada['env'] == 'jobmanager':
            from nasajon.jobmanager.resources.envconfig import EnvConfig
            env_config = EnvConfig.instance()
            self.erp_user = entrada['erp_user']
            self.erp_password = entrada['erp_password']

        self.database_host = env_config.database_host
        self.database_name = env_config.database_name
        self.database_port = env_config.database_port
        self.parametro_execucao = parametro_execucao
        
    
    def executar(self):
        params = [
            self.exe_service_document,
            self.autoexec,
            self.database_host,
            self.database_name,
            self.database_port,
            self.erp_user,
            self.erp_password, 
            self.parametro_execucao
        ]
        if self.dir_instalacao[:1] == '\\':
            os.system(f'pushd {self.dir_instalacao}')
        else:
            os.chdir(self.dir_instalacao)
        os.system(" ".join(params))