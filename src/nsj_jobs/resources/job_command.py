from nsj_jobs.resources.db_adapter import DBAdapter
from nsj_jobs.resources.envconfig import EnvConfig
from nsj_jobs.resources.log import Log

import json 
import os.path
import sys
import traceback


class JobCommand:

    # def __init__(self):
    # self._http_wrapper = HttpWrapper()
    # self._smtp_wrapper_class = SmtpWrapper
    # self._relatorio_service_class = RelatorioService
    # self._time_service = TimeService.get_instancia()

    def execute_cmd(self, entrada = None):
        """
        TODO Documentar...
        """
        db = None
        log = None
        try:
            db = DBAdapter()

            log = Log(type(self).__name__, db)

            log.debug("Iniciando...")

            # entrada = None
            # if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            #   with open(sys.argv[1], 'r') as f:
            #        entrada = json.load(f)
            # else:
            #    arquivo_json = sys.argv[0]
            #    arquivo_json = arquivo_json[0:len(arquivo_json)-3]
            #    arquivo_json = arquivo_json+".json"
            #    if os.path.exists(arquivo_json):
            #        with open(arquivo_json, 'r') as f:
            #            entrada = json.load(f)

            # entrada = dict()
            if len(sys.argv) > 1 and entrada is None:
                entrada = json.loads(sys.argv[0])

            log.debug("Entrada a seguir:")
            log.debug(entrada)

            log.debug("Iniciando código do job.")

            retorno = self.execute(entrada, None, db, log, log)
            print(retorno)

            log.debug("Saída da execução a seguir:")
            log.debug(retorno)

            sys.exit(0)
        except Exception as e:
            if log is not None:
                log.excecao(str(e))

            print(str(e))
            traceback.print_exc()
            sys.exit(1)
        finally:
            if db is not None:
                db.close()

    def execute(self, entrada: dict, job, db, log, registro_execucao):
        return ''
