import os
import time


delay = os.getenv("frequencia_job", 300) # 5 minutos por padrão

while True:
    os.system("python -m nsj_jobs.emissao_nota")
    time.sleep(delay)
