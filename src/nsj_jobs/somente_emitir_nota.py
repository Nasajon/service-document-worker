from nsj_jobs.resources.job_command import JobCommand
from nsj_jobs.service_document_cmd import ServiceDocumentCMD
from nsj_jobs.dao import DAO

class EmissaoNota(JobCommand):
    def __init__(self):
        self.banco = None
        self.nota_fiscal = None
        self.registro_execucao = None
        
    
    def execute(self, entrada: dict, job, db, log, registro_execucao):
        self.registro_execucao = registro_execucao
        self.banco = DAO(db)
        registro_execucao.informativo('Iniciando processo de emissão de nota fiscal.')
        # dirInstalacaoERP = self.banco.dir_instalacao_erp.obterDiretorioInstalacao()
        dirInstalacaoERP = "C:\\Nasajon Sistemas\\Integratto2\\"
        serviceDocument = ServiceDocumentCMD(dirInstalacaoERP, entrada, 'SOMENTE_EMISSAO')
        serviceDocument.executar()
        registro_execucao.informativo('Processo de emissão finalizado.')
        

    
if __name__ == '__main__':
   EmissaoNota().execute_cmd({'env':'docker'})