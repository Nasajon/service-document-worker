import os
import time
from multiprocessing import Process

def call_emission_routine():
    delay = os.getenv("frequencia_job", 120) # 2 minutos por padrão

    while True:
        os.system("python -m nsj_jobs.somente_emitir_nota")
        time.sleep(delay)


def call_import_routine():
    delay = os.getenv("frequencia_job", 300) # 5 minutos por padrão

    while True:
        os.system("python -m nsj_jobs.somente_importar_nota")
        time.sleep(delay)

if __name__ == '__main__':
    emission = Process(target=call_emission_routine)
    importation = Process(target=call_import_routine)
    importation.start()
    emission.start()
