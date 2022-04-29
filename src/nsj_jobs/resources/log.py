# !/usr/bin/env python
# -*- coding: cp1252 -*-
from nsj_jobs.resources.envconfig import EnvConfig

import datetime
import enum
import os
import pathlib
import time
import threading
import traceback
import json


class LogLevel(enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    ATENCAO = "ATENCAO"
    ERRO = "ERRO"
    NONE = "NONE"


class Log:

    LINHA_PADRAO = "{} - {} - {} - {}"

    def __init__(self, nome_log: str, db):
        self._file = None
        self._open_log_file(nome_log)
        self._lock_escrita = threading.Lock()
        self._db = db
        self._nome_log = nome_log

    def debug(self, msg: str, print_traceback: bool = False):
        """
        Escreve uma mensagem para debug no log.
        """
        msg = msg.__str__()
        env_log_level = LogLevel(EnvConfig.instance().log_level)
        if (env_log_level == LogLevel.DEBUG):
            self._log(LogLevel.DEBUG, msg, print_traceback, False)

    def info(self, msg: str, print_traceback: bool = False):
        """
        Escreve uma mensagem informativa no log.
        """

        print(msg)  # TODO

        msg = msg.__str__()
        env_log_level = LogLevel(EnvConfig.instance().log_level)
        if (
                (env_log_level == LogLevel.DEBUG) or
                (env_log_level == LogLevel.INFO)
        ):
            self._log(LogLevel.INFO, msg, print_traceback, False)

    def atencao(self, msg: str, print_traceback: bool = False):
        """
        Escreve uma mensagem de aten��o no log.
        """
        msg = msg.__str__()
        env_log_level = LogLevel(EnvConfig.instance().log_level)
        if (
                (env_log_level == LogLevel.DEBUG) or
                (env_log_level == LogLevel.INFO) or
                (env_log_level == LogLevel.ATENCAO)
        ):
            self._log(LogLevel.ATENCAO, msg, print_traceback, False)

    def erro(self, msg: str, print_traceback: bool = False):
        """
        Escreve uma mensagem de erro no log.
        """
        msg = msg.__str__()
        print(msg)  # TODO
        print(traceback.format_stack())
        env_log_level = LogLevel(EnvConfig.instance().log_level)
        if (
                (env_log_level == LogLevel.DEBUG) or
                (env_log_level == LogLevel.INFO) or
                (env_log_level == LogLevel.ATENCAO) or
                (env_log_level == LogLevel.ERRO)
        ):
            self._log(LogLevel.ERRO, msg, print_traceback, False)

    def excecao(self, msg: str, print_exception_trace: bool = True):
        """
        Escreve uma mensagem de erro, originado por uma exce��o, no log.
        """
        msg = msg.__str__()
        print(msg)  # TODO
        print(traceback.format_exc())
        env_log_level = LogLevel(EnvConfig.instance().log_level)
        if (
                (env_log_level == LogLevel.DEBUG) or
                (env_log_level == LogLevel.INFO) or
                (env_log_level == LogLevel.ATENCAO) or
                (env_log_level == LogLevel.ERRO)
        ):
            self._log(LogLevel.ERRO, msg, False, print_exception_trace)

    def flush(self):
        self._lock_escrita.acquire()
        try:
            self._file.flush()
        finally:
            self._lock_escrita.release()

    def _log(self, tipo: LogLevel, msg: str, print_traceback: bool, print_exception_trace: bool):
        pass
        # sql = "insert into log (nome_job, texto, level) values (%s, %s, %s)"

        # self._lock_escrita.acquire()
        # try:
        #     data_hora = str(datetime.datetime.now())
        #     linha = Log.LINHA_PADRAO.format(
        #         data_hora, EnvConfig.instance().id_execucao, tipo.value, msg)

        #     self._file.write(linha + "\n")
        #     print(linha)
        #     if (self._db != None):
        #         self._db.execute(sql, [self._nome_log, msg, tipo.value])

        #     if (print_traceback):
        #         trace = traceback.format_stack()
        #         trace_str = ""
        #         for tr in trace:
        #             trace_str += tr + "\n"
        #         self._file.write(trace_str)
        #         print(trace)
        #         if (self._db != None):
        #             self._db.execute(
        #                 sql, [self._nome_log, msg+' | '+trace_str, tipo.value])

        #     if (print_exception_trace):
        #         trace = traceback.format_exc()
        #         self._file.write(trace)
        #         print(trace)
        #         if (self._db != None):
        #             self._db.execute(
        #                 sql, [self._nome_log, msg+' | '+trace, tipo.value])
        # finally:
        #     self._lock_escrita.release()

    def _open_log_file(self, nome_log: str):
        """
        Verifica as condi��es b�sicas para abrir o arquivo de log para escrita
        (diret�rio base, se deve apagar um arquivo de log anterior e recriar, etc).

        É importante destacar que se utiliza um estrat�gia de log rotativo por dia,
        (isto �, no m�ximo haver�o 31 arquivos de log no diret�rio, pois a cada dia
        do m�s � criado um arquivo com nome no padr�o "log_<DIA>.txt", e assim o log
        mais antigo disponível deve datar de um m�s antes).
        """

        # Recuperando o diret�rio de logs:
        dir_log = pathlib.Path(EnvConfig.instance().log_path)

        # Verificando se o diret�rio de log existe (e criando, caso constr�rio):
        if not os.path.exists(dir_log):
            os.makedirs(dir_log)

        # Resolvendo o nome do arquivo:
        file_name = "log_" + nome_log + "_" + \
            str(datetime.datetime.now().day) + ".txt"

        # Resolvendo o path do arquivo:
        file_log = dir_log / file_name

        # Verificando se o arquivo existe:
        if os.path.isfile(file_log):
            # Recuperando a data de modifica��o do arquivo:
            data_modificacao = datetime.datetime.fromtimestamp(
                os.path.getmtime(file_log))

            # Excluindo o arquivo se n�o for de hoje:
            if (data_modificacao.date() < datetime.datetime.now().date()):
                os.remove(file_log)

        # Abrindo o arquivo em modo de concatena��o (append):
        self._file = open(file_log, "a")

    def __del__(self):
        self._file.close()

    # C�digo do RegistroExecucaoDao. Somente para mock, pois n�o tem como salvar na tabela de log do jobmanager por fora do jobmanager

    def informativo(self, mensagem):
        self._file.writelines(mensagem)

    def erro_execucao(self, mensagem, grava_exception_trace: bool = False):
        pass

    def exception_execucao(self, mensagem):
        pass
