ARG WINDOWS_VERSION=1809
FROM mcr.microsoft.com/windows:${WINDOWS_VERSION}
MAINTAINER Nasajon <devops@nasajon.com.br>

USER ContainerAdministrator
RUN curl https://www.python.org/ftp/python/3.10.4/python-3.10.4-amd64.exe -o python_installer.exe
RUN python_installer.exe /passive InstallAllUsers=1 PrependPath=1 Include_test=0
RUN python -m pip install psycopg2
RUN mkdir C:\notas
RUN mkdir C:\notas\output

ARG dir_instalacao_nasajon_src="erp-instalador/bin/integratto"
ARG dir_instalacao_nasajon_target="C:/Nasajon Sistemas/Integratto2"
ARG dir_job_src="src/"
ARG dir_job_target="C:/ServiceDocumentWorker/"

COPY ${dir_instalacao_nasajon_src} ${dir_instalacao_nasajon_target}
COPY ${dir_job_src} ${dir_job_target}
COPY nsjServiceDocumentEngine.exe ${dir_instalacao_nasajon_target}
COPY entrypoint.py C:/

ENV PYTHONPATH=C:\\ServiceDocumentWorker

# RUN schtasks /create /sc minute /tn emissao_nota /mo 1 /ru ContainerAdministrator /tr "python -m nsj_jobs.emissao_nota"

ENTRYPOINT python entrypoint.py