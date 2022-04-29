from nsj_jobs.resources.envconfig import EnvConfig

import psycopg2
import uuid


class DBAdapter:

    def __init__(self):
        self._db = psycopg2.connect(
            host=EnvConfig.instance().database_host,
            database=EnvConfig.instance().database_name,
            user=EnvConfig.instance().database_user,
            password=EnvConfig.instance().database_password,
            port=EnvConfig.instance().database_port
        )
        self._db.autocommit = True

        self._is_open = True

    def close(self):
        """
        Fecha a conexão com o banco de dados (aberta ao se construir o adapter),
        se a mesma não foi fechada antes.
        """

        if (self._is_open):
            self._db.close()
            self._is_open = False

    def execute(self, sql: str, parameters=None) -> None:
        """
        Executando uma instrução sql sem retorno.

        É obrigatório a passagem de uma conexão de banco no argumento self._db.
        """

        try:
            cur = self._db.cursor()
            self._execute(cur, sql, parameters)
        finally:
            cur.close()

    def execute_query(self, sql: str, model_class: object, parameters=None) -> list:
        """
        Executando uma instrução sql com retorno.

        O retorno é feito em forma de uma lista (list), com elementos do tipo passado pelo parâmetro
        "model_class".

        É importante destacar que para cada coluna do retorno, será procurado um atributo no model_class
        com mesmo nome, para setar o valor. Se este não for encontrado, a coluna do retorno é ignorada.
        """

        result = []
        try:
            cur = self._db.cursor()
            self._execute(cur, sql, parameters)
            rs = cur.fetchall()

            for rec in rs:
                model = model_class()

                i = 0
                for column in cur.description:
                    attribute = column.name

                    if (hasattr(model, attribute)):
                        setattr(model, attribute, rec[i])

                    i += 1

                result.append(model)

        finally:
            cur.close()

        return result

    def execute_query_to_dict(self, sql: str, parameters=None) -> list:
        """
        Executando uma instrução sql com retorno.

        O retorno é feito em forma de uma lista (list), com elementos do tipo dict (onde cada chave é igual ao
        nome do campo correspondente).
        """

        result = []
        try:
            cur = self._db.cursor()
            self._execute(cur, sql, parameters)
            rs = cur.fetchall()

            for rec in rs:
                item = dict()

                i = 0
                for column in cur.description:
                    attribute = column.name

                    item[attribute] = rec[i]

                    i += 1

                result.append(item)

        finally:
            cur.close()

        return result

    def execute_query_single_result(self, sql: str, model_class: object, parameters=None) -> "model_class":
        """
        Executando uma instrução sql com retorno.

        O retorno é feito em forma de um objeto do tipo passado pelo parâmetro "model_class".

        É importante destacar que para cada coluna do retorno, será procurado um atributo no model_class
        com mesmo nome, para setar o valor. Se este não for encontrado, a coluna do retorno é ignorada.
        """

        result = None
        try:
            cur = self._db.cursor()
            self._execute(cur, sql, parameters)
            rs = cur.fetchall()

            if (len(rs) > 0):
                model = model_class()

                i = 0
                for column in cur.description:
                    attribute = column.name

                    if (hasattr(model, attribute)):
                        setattr(model, attribute, rs[0][i])

                    i += 1

                result = model

        finally:
            cur.close()

        return result

    def get_single_result(self, sql: str, parameters=None):
        """
        Executa uma instrução SQL para a qual se espera um único retorno (com tipo primitivo). Exemplo:
        select 1+1

        Se não houver retorno, retorna None.
        """

        result = None
        try:
            cur = self._db.cursor()
            self._execute(cur, sql, parameters)
            rs = cur.fetchall()

            if (len(rs) > 0):
                result = rs[0][0]
        finally:
            cur.close()

        return result

    def _check_type(self, parameter):
        if (isinstance(parameter, uuid.UUID)):
            return str(parameter)
        else:
            return parameter

    def _execute(self, cursor, sql: str, parameters: list):
        pars = None

        if (parameters != None):
            pars = [self._check_type(par) for par in parameters]

        cursor.execute(sql, pars)

    def __del__(self):
        """
        Garante o fechamento da conexão por meio do destrutor.
        """

        if (hasattr(self, "_db")):
            self._db.close()
