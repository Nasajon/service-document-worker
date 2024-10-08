# !/usr/bin/env python
# -*- coding: cp1252 -*-

import copy
from decimal import Decimal
from nsj_jobs.resources.db_adapter import DBAdapter
from datetime import datetime
import enum

IsEmpty = ""


def quotedString(value: str):
    return "'" + value + "'"


def converter_modalidade_numero(modalidade: str):
    de_para = {
        "por_conta_do_remetente": 0,
        "por_conta_do_destinatario": 1,
        "por_conta_de_terceiros": 2,
        "sem_frete": 3,
        "transporte_proprio_remetente": 4,
        "transporte_proprio_destinatario": 5,
    }
    return de_para[modalidade]


class tipoMsg(enum.Enum):
    sucesso = 0
    erro = 1
    inconsistencia = 2
    serviceDocument = 3


class Status(enum.Enum):
    Aberto = 0
    Emitido = 1
    Rejeitado = 2
    Reemitir = 3
    Cancelamento_Cliente = 4
    Cancelamento_Fiscal = 5
    Cancelado = 6


class StatusDocumento(enum.Enum):
    sdcAberto = 0
    sdcProcessado = 1
    sdcTransmitido = 2
    sdcRespondido = 3
    sdcExportado = 4
    sdcErroProcessamento = 5
    sdcErroEmissao = 6
    sdcPendenteConsulta = 7
    sdcConsultado = 8
    sdcErroConsulta = 9
    sdcRespondidoComFalha = 10
    sdcDavGerado = 11
    sdcDavProcessado = 12
    sdcImportado = 13
    sdcErroImportacao = 14


class Tp_Operacao(enum.Enum):
    ProdutorRural = 1
    Outros = 3
    ConsumidorFinal = 12
    Varejista = 23
    Atacadista = 24
    Industria = 25
    ConsFinalSemST = 26


class registra_log:
    def __init__(self, conexao_banco: DBAdapter = None):
        self.conexao = conexao_banco

    def mensagem(self, id_pedido: str, msg: str, tipo: tipoMsg, id_docserv_msg=None):

        if id_docserv_msg != None:
            var_id_doc_msg = str(id_docserv_msg)
        else:
            var_id_doc_msg = None

        if id_pedido == IsEmpty or id_pedido is None:
            return None

        valor_Tipo = tipo.value

        if self.pode_gravar(id_pedido, msg, valor_Tipo):
            sql = "Insert into servicedocument.log_execucaojob(id_pedido, mensagem, tipo, id_doc_service_msg ) Values(%s, %s, %s, %s)"
            sql = sql
            self.conexao.execute(sql, [id_pedido, msg, tipo.value, var_id_doc_msg])
        else:
            sql = """Update servicedocument.log_execucaojob set ultimaexecucao = %s
                    where id_pedido = %s and tipo = %s and mensagem = %s"""

            sql = sql
            self.conexao.execute(sql, [datetime.now(), id_pedido, valor_Tipo, msg])

    def pode_gravar(self, id_pedido: str, msg: str, tipo: int):

        sql = """ SELECT Count(1) as valor FROM servicedocument.log_execucaojob l
                WHERE l.id_pedido = %s AND l.tipo = %s AND l.mensagem  = %s"""

        sql = sql
        qry = self.conexao.execute_query_to_dict(sql, [id_pedido, tipo, msg])

        return qry[0]["valor"] == 0


class xml_service_document:
    def __init__(self, conexao_banco: DBAdapter = None):
        self.conexao = conexao_banco

    def obterCaminhoArquivo(self, valorcampo, aplicacao):
        sql = """SELECT c.valor 
                FROM ns.configuracoes c 
                WHERE c.campo = %s AND 
                aplicacao = %s
                Limit 1"""

        qry = self.conexao.execute_query_to_dict(sql, [valorcampo, aplicacao])
        if len(qry) == 0:
            return None
        elif (qry[0]["valor"] is None) or (qry[0]["valor"] == IsEmpty):
            return None
        else:
            return qry[0]["valor"]
        
    def retentar_emissao(self):
        # 36 é este worker
        sql = """SELECT c.valor 
                FROM ns.configuracoes c 
                WHERE c.campo = 1 AND 
                aplicacao = 36
                Limit 1"""

        qry = self.conexao.execute_query_to_dict(sql, [])
        if len(qry) == 0:
            return None
        elif (qry[0]["valor"] is None) or (qry[0]["valor"] == IsEmpty):
            return None
        else:
            return int(qry[0]["valor"])


class dir_instalacao_erp:
    def __init__(self, conexao_banco: DBAdapter = None):
        self.conexao = conexao_banco

    def obterDiretorioInstalacao(self):
        sql = """SELECT c.valor 
                FROM ns.configuracoes c 
                WHERE c.campo = 2 AND 
                aplicacao = 0
                Limit 1"""

        qry = self.conexao.execute_query_to_dict(sql, [])
        if len(qry) == 0:
            return None
        elif (qry[0]["valor"] is None) or (qry[0]["valor"] == IsEmpty):
            return None
        else:
            return qry[0]["valor"]


class Tpedidos:
    def __init__(self, conexao_banco: DBAdapter = None):
        self.conexao = conexao_banco

    def obterPedidos(self, situacao: list, processado: bool, limit: bool):
        strSituacao = IsEmpty
        if situacao.count == 1:
            strSituacao = situacao[0]
        else:
            for sCod in situacao:
                if strSituacao == IsEmpty:
                    strSituacao = str(sCod.value)
                else:
                    strSituacao = strSituacao + "," + str(sCod.value)

        sql = (
            """SELECT ID_PEDIDO, NUM_PEDIDO, NUM_EXTERNO, STATUS,
                OBSERVACAO, COALESCE( (SELECT o.operacao FROM ESTOQUE.operacoes o
                WHERE lower(o.codigo) = lower(ped.cod_operacao) 
                )::VARCHAR(30), '') AS ID_OPERACAO,
                upper(COD_OPERACAO) AS OPERACAO,
                TP_OPERACAO, TIPODOCUMENTO, SERIE_NF,
                '00' 		AS SUBSERIE,
                DT_EMISSAO 	AS DATASAIDAENTRADA,
                DT_EMISSAO	AS DATALANCAMENTO,
                LOCALESTOQUE,
                CFOP,
                TENTATIVAS_ADICIONAIS, 
                PRIMEIRA_TENTATIVA                             
                FROM servicedocument.PEDIDOS  PED
                WHERE PED.STATUS in ("""
            + strSituacao
            + """) and
                PED.Processado = %s
                AND PED.EMITIR = TRUE
                ORDER BY PED.data_hora_criacao"""
            + (" LIMIT 10" if limit else "")
        )

        sql = sql
        return self.conexao.execute_query_to_dict(sql, [processado])

    def obterPedidos_Processados(self, situacao: list):
        strSituacao = IsEmpty
        if situacao.count == 1:
            strSituacao = situacao[0]
        else:
            for sCod in situacao:
                if strSituacao == IsEmpty:
                    strSituacao = str(sCod.value)
                else:
                    strSituacao = strSituacao + "," + str(sCod.value)

        sql = (
            """SELECT ID_PEDIDO, NUM_PEDIDO, NUM_EXTERNO, STATUS, TENTATIVAS_ADICIONAIS, PRIMEIRA_TENTATIVA, ULTIMA_TENTATIVA, datahora_processamento, emitir_nota
                FROM servicedocument.PEDIDOS  PED
                WHERE PED.STATUS in ("""
            + strSituacao
            + """) and
                PED.Processado = True
                AND PED.EMITIR = True
                And Ped.chave_de_acesso Is null
                ORDER BY PED.data_hora_criacao"""
        )

        sql = sql
        return self.conexao.execute_query_to_dict(sql)


class Tpedido:
    def __init__(self, conexao_banco: DBAdapter = None):
        self.conexao = conexao_banco
        self.registraLog = registra_log(conexao_banco)

        self.pedido = None
        self.lstEstabelecimento = None
        self.lstCliente = None
        self.lstEndCliente = None
        self.endEntrega = None
        self.endPrestacao = None
        self.lstProdutos = None
        self.lstVolumes = None
        self.lstServicos = None
        self.lstFormaPagamento = None

        self.camposAtualizar = {
            "chave_de_acesso": None,
            "numero_nf": None,
            "id_docfis": None,
            "status": None,
            "mensagem": None,
            "id_doc_serv_msg": None,
        }

    def id_pedido(self):
        if self.pedido["id_pedido"] == IsEmpty or self.pedido["id_pedido"] is None:
            return IsEmpty
        else:
            return str(self.pedido["id_pedido"])

    def id_cliente(self):
        if self.lstCliente["id_cliente"] is None:
            self.lstCliente = self.obterCliente

        return str(self.lstCliente["id_cliente"])

    def id_estabecimento(self):
        if self.lstEstabelecimento["id_estabelecimento"] is None:
            self.lstEstabelecimento = self.obterEstabelecimento

        return str(self.lstEstabelecimento["id_estabelecimento"])

    def status(self):
        if self.id_pedido == IsEmpty:
            return -1
        else:
            return int(self.pedido["status"])

    def num_pedido(self):
        if (self.pedido["num_pedido"] is None) or (
            self.pedido["num_pedido"] == IsEmpty
        ):
            return None
        else:
            return self.pedido["num_pedido"]

    def NumPedidoFormatado(self):
        numPedido = self.num_pedido
        if numPedido != None:
            return "%030d" % (numPedido,)
        else:
            return None

        return str(numPedido)

    def retornaPedido(self):
        return self.pedido

    def retornaProdutos(self):
        if self.lstProdutos is None:
            return self.obterProdutos
        else:
            return self.lstProdutos

    def atualizar(self):
        id = self.id_pedido
        if id != IsEmpty:
            self.obterPedidoId(id)

    def obterPedidoId(self, id_pedido):
        if id_pedido == IsEmpty or id_pedido is None:
            return None

        sql = """SELECT 
                ID_PEDIDO,
                CNPJ_CLIENTE,
                CNPJ_ESTABELECIMENTO,
                upper(COD_OPERACAO) AS OPERACAO,
                DT_EMISSAO,
                DT_EMISSAO 	AS DATASAIDAENTRADA,
                COALESCE(DATA_LANCAMENTO, DT_EMISSAO) AS DATALANCAMENTO,
                NUM_PEDIDO,
                NUM_EXTERNO,
                case when CONSUMIDORFINAL is not null 
                    then case when CONSUMIDORFINAL 
                        then '1' 
                        else '23' 
                        end 
                    else '' 
                    end as  CONSUMIDORFINAL,
                VALOR_PEDIDO,
                STATUS,
                OBSERVACAO,
                COALESCE( (SELECT o.operacao FROM ESTOQUE.operacoes o
                WHERE lower(o.codigo) = lower(ped.cod_operacao) 
                )::VARCHAR(30), '') AS ID_OPERACAO,
                TP_OPERACAO,
                TIPODOCUMENTO,
                '000' AS FORMAPAGAMENTO,
                SERIE_NF,
                COALESCE(SUBSERIE_NF, '00') AS SUBSERIE,
                MUNICIPIO_GERADOR,
                LOCALESTOQUE,
                CFOP,
                TENTATIVAS_ADICIONAIS, 
                PRIMEIRA_TENTATIVA,
                TIPO_NOTA,
                EMITIR_NOTA,
                MODALIDADE_FRETE,
                TRANSPORTADORA,
                case when VENDAPRESENCIAL then '1' else '' end as VENDAPRESENCIAL                                       
                FROM servicedocument.PEDIDOS PED WHERE PED.id_pedido = %s"""

        sql = sql
        pedidos = self.conexao.execute_query_to_dict(sql, [id_pedido])
        if len(pedidos) == 0:
            return None
        else:
            self.obterDadosPedido(id_pedido)
            self.pedido = pedidos[0]
            if self.pedido.get("tipo_nota") == "NFSE":
                self.ajustarFormaPagamentoNFSE()

    def obterDadosPedido(self, idpedido: str):

        self.lstEstabelecimento = self.obterEstabelecimento(idpedido)
        self.lstCliente = self.obterCliente(idpedido)

        if len(self.lstCliente) != 0:
            var_id_cliente = str(self.lstCliente[0]["id_cliente"])
            self.lstEndCliente = self.obterEnderecoCliente(var_id_cliente)

        self.endEntrega = self.obterEnderecoEntrega(idpedido)
        self.endPrestacao = self.obterEnderecoPrestacao(idpedido)
        self.lstProdutos = self.obterProdutos(idpedido)
        self.lstVolumes = self.obterVolumes(idpedido)
        self.lstServicos = self.obterServicos(idpedido)
        self.lstFormaPagamento = self.obterFormasPagamentos(idpedido)

    def ajustarFormaPagamentoNFSE(self):
        pagamentos = copy.deepcopy(self.lstFormaPagamento)
        novaLista = {}
        for pagamento in pagamentos:
            if pagamento.get("tipoformapagamento") not in novaLista.keys():
                novaLista[pagamento.get("tipoformapagamento")] = {
                    "tipoformapagamento": pagamento.get("tipoformapagamento"),
                    "parcelas": [],
                    "valor_total": Decimal("00"),
                }
            novaLista[pagamento.get("tipoformapagamento")]["parcelas"].append(
                {
                    "numero": pagamento.get("numero"),
                    "vencimento": pagamento.get("dt_vencimento"),
                    "valor": pagamento.get("valor_parcela"),
                }
            )
            novaLista[pagamento.get("tipoformapagamento")][
                "valor_total"
            ] += pagamento.get("valor_parcela")

        self.lstFormaPagamento = [novaLista[i] for i in novaLista.keys()]

    def updateSituacao(self, status_value: int):
        idpedido = self.pedido["id_pedido"]
        if idpedido != IsEmpty:
            sql = "update servicedocument.pedidos set status = %s where id_pedido = %s"
            sql = sql
            self.conexao.execute(sql, [status_value, idpedido])

    def updatePedidoProcessado(self, idPedido):
        if idPedido != IsEmpty:
            sql = """UPDATE servicedocument.pedidos SET
                processado = TRUE,
                datahora_processamento = current_timestamp 
            WHERE id_pedido = %s"""

            sql = sql
            self.conexao.execute(sql, [idPedido])

    def updatePedido(self):
        idpedido = self.pedido["id_pedido"]
        if idpedido == IsEmpty or idpedido is None:
            return
        else:
            chave_de_acesso = self.camposAtualizar.get("chave_de_acesso")
            numero_nf = self.camposAtualizar.get("numero_nf")
            serie_nf = self.camposAtualizar.get("serie_nf")
            iddocfis = self.camposAtualizar.get("id_docfis")
            novoStatus = self.camposAtualizar.get("status")
            msgAviso = self.camposAtualizar.get("mensagem")
            iddocservmsg = self.camposAtualizar.get("id_doc_serv_msg")

            if novoStatus is None:
                return

            if msgAviso is None:
                msgAviso = IsEmpty

            sql = (
                """update servicedocument.pedidos set
            chave_de_acesso = %s , 
            numero_nf = %s ,
            serie_nf = %s , 
            id_docfis = %s , 
            status = %s , 
            mensagem =  %s 
            where id_pedido= %s """
            )

            self.conexao.execute(
                sql,
                [
                    chave_de_acesso,
                    numero_nf,
                    serie_nf,
                    iddocfis,
                    novoStatus,
                    msgAviso,
                    idpedido,
                ],
            )
            self.registraLog.mensagem(
                idpedido, msgAviso, tipoMsg.serviceDocument, iddocservmsg
            )

    def atualizarTentativa(
        self, primeira_tentativa, ultima_tentativa, tentativa_adicional=0
    ):
        idpedido = self.pedido["id_pedido"]
        if idpedido == IsEmpty or idpedido is None:
            return
        else:
            novoStatus = Status.Reemitir.value
            if tentativa_adicional == 0:
                msgAviso = "Atualizando data e hora da primeira tentativa, que falhou."
                processado = True
            else:
                processado = False
                msgAviso = f"Gerando XML novamente de forma automática para a {tentativa_adicional+1}º tentativa de emissão."

            sql = (
                """update servicedocument.pedidos set
                status = %s ,
                tentativas_adicionais = %s ,
                primeira_tentativa = %s ,
                ultima_tentativa = %s ,
                processado = %s
                where id_pedido = %s """
            )

            self.conexao.execute(
                sql,
                [
                    novoStatus,
                    tentativa_adicional,
                    primeira_tentativa,
                    ultima_tentativa,
                    processado,
                    idpedido,
                ],
            )
            self.registraLog.mensagem(idpedido, msgAviso, tipoMsg.sucesso)

    def registrarPrimeiraTentativaParaReemissao(self):
        idpedido = self.pedido["id_pedido"]
        if idpedido == IsEmpty or idpedido is None:
            return
        else:
            novoStatus = Status.Reemitir.value

            sql = (
                """update servicedocument.pedidos set
                status = %s ,
                primeira_tentativa = %s
                where id_pedido = %s """
            )

            self.conexao.execute(sql, [novoStatus, datetime.now(), idpedido])

    def obterProdutos(self, id_pedido):
        if id_pedido == IsEmpty or id_pedido is None:
            return None

        campos = """COALESCE(PROD.CODIGO, ITE.COD_PRODUTO) AS COD_PRODUTO,
                    (CASE WHEN PROD.CODIGO IS NULL THEN 1 ELSE 0 END) AS PROD_NAO_EXISTE,
                    (CASE WHEN ITE.ESPECIFICACAO IS NULL THEN PROD.ESPECIFICACAO ELSE ITE.ESPECIFICACAO end) as ESPECIFICACAO,
                    PROD.TIPI, 
                    ITE.QUANTIDADE,
                    (SELECT u.codigo FROM estoque.unidades u
                    WHERE u.unidade = PROD.unidadedemedida) AS COD_UNIDADE,
                    ITE.VALOR_UNITARIO,
                    ROUND( (ITE.VALOR_UNITARIO * ITE.QUANTIDADE), 2) AS VALORTOTALBRUTO,
                    LOCALESTOQUE,
                    (SELECT F.CODIGO FROM ESTOQUE.FIGURASTRIBUTARIAS F 
                    WHERE F.FIGURATRIBUTARIA = PROD.FIGURATRIBUTARIA
                    ) 		AS FIGURATRIBUTARIA,
                    ITE.CFOP,
                    ITE.DOCUMENTOREFERENCIADO_CHAVE,
                    ITE.VALOR_FRETE	AS VALORFRETE,
                    0.00	AS VALORSEGURO,
                    0.00	AS VALOROUTRASDESPESAS,
                    ITE.valor_desconto AS VALORDESCONTO,"""

        sql = (
            """
            with produtos as (
	        select ite.id_item_pedido,  prod.*, (coalesce(prod.codigodebarras,'') = ite.cod_produto) as cod_barra_igual, ROW_NUMBER() OVER( partition by id_item_pedido    ORDER BY ite.id_item_pedido, (coalesce(prod.codigodebarras,'') = ite.cod_produto) desc) rec_num
            FROM servicedocument.ITENSPEDIDOS ITE
            LEFT JOIN ESTOQUE.PRODUTOS PROD ON ( UPPER(PROD.CODIGO) = UPPER(ITE.COD_PRODUTO) or  UPPER(PROD.codigodebarras) = UPPER(ITE.COD_PRODUTO) )
            WHERE ITE.ID_PEDIDO = %s and not ite.generico
            order by ite.id_item_pedido,  (coalesce(prod.codigodebarras,'') = ite.cod_produto) desc
            )
            SELECT
              """
            + campos
            + """
                    0 as SEM_SALDO, 
                    '' AS MENSAGEM_ERRO
                    FROM servicedocument.ITENSPEDIDOS ITE
                    LEFT JOIN produtos PROD on ite.id_item_pedido = prod.id_item_pedido and prod.rec_num = 1         
                    WHERE ITE.ID_PEDIDO = %s and not ite.generico
                    ORDER BY ITE.COD_PRODUTO"""
        )

        sql = sql
        lstPedidos = self.conexao.execute_query_to_dict(sql, [id_pedido, id_pedido])

        sql = (
            """SELECT 
              """
            + campos
            + """
                    (CASE WHEN ITE.sem_saldo THEN 1 ELSE 0 END) as sem_saldo, 
                    coalesce(ITE.MENSAGEM_ERRO, '') as mensagem_erro
                    FROM estoque.recupera_produtos_especificos_de_produto_generico(%s) ITE
                    LEFT JOIN ESTOQUE.PRODUTOS PROD ON ( UPPER(PROD.CODIGO) = UPPER(ITE.COD_PRODUTO))
                    ORDER BY ITE.COD_PRODUTO"""
        )

        lstPedidosGenericos = self.conexao.execute_query_to_dict(sql, [id_pedido])

        return lstPedidos + lstPedidosGenericos

    def obterServicos(self, id_pedido):
        if id_pedido == IsEmpty or id_pedido is None:
            return None

        sql = """SELECT
                cod_produto as codigo,
                quantidade,
                valor_unitario,
                valor_desconto
                FROM servicedocument.ITENSPEDIDOS ITE
                WHERE ITE.ID_PEDIDO = %s
                ORDER BY ITE.COD_PRODUTO"""

        sql = sql
        lstServicos = self.conexao.execute_query_to_dict(sql, [id_pedido])

        return lstServicos

    def obterVolumes(self, id_pedido):
        if id_pedido == IsEmpty or id_pedido is None:
            return None

        sql = """SELECT
                NUMERACAO,
                MARCA,
                ESPECIE,
                QUANTIDADE,
                PESO_BRUTO,
                PESO_LIQUIDO
                FROM servicedocument.VOLUMES_PEDIDOS
                WHERE ID_PEDIDO = %s
                ORDER BY NUMERACAO"""

        sql = sql
        lstVolumes = self.conexao.execute_query_to_dict(sql, [id_pedido])

        return lstVolumes

    def obterEstabelecimento(self, id_pedido):
        sql = """SELECT 
                    EMP.EMPRESA     AS ID_EMPRESA,
                    EST.ESTABELECIMENTO  AS ID_ESTABELECIMENTO,
                    EMP.CODIGO 	    AS EMPRESA,
                    EST.CODIGO 	    AS ESTABELECIMENTO,
                    GRU.CODIGO 		AS GRUPOEMPRESARIAL
                    FROM NS.EMPRESAS EMP
                    INNER JOIN NS.ESTABELECIMENTOS EST ON EST.EMPRESA = EMP.EMPRESA 
                    LEFT  JOIN NS.GRUPOSEMPRESARIAIS GRU ON (GRU.GRUPOEMPRESARIAL = EMP.GRUPOEMPRESARIAL)
                    INNER JOIN servicedocument.PEDIDOS PED  ON ( (EST.RAIZCNPJ || EST.ORDEMCNPJ) = PED.CNPJ_ESTABELECIMENTO ) 
                    WHERE ped.id_pedido = %s"""

        sql = sql
        qry = self.conexao.execute_query_to_dict(sql, [id_pedido])
        if len(qry) == 0:
            return None
        else:
            return qry

    def obterCliente(self, id_pedido):
        sql = """SELECT                 
                    PESS.ID				AS ID_CLIENTE, 
                    PESS.PESSOA 		AS CODIGO,
                    PESS.CHAVECNPJ		AS CPF_CNPJ,
                    PESS.NOME	        AS NOME,
                    PESS.NOMEFANTASIA,
                    PESS.EMAIL,
                    coalesce(PESS.inscricaoestadual, '') as inscricaoestadual,
                    (CASE WHEN PESS.indicadorinscricaoestadual = 1 then TRUE ELSE FALSE end) as contribuinteICMS
                    FROM NS.PESSOAS   PESS
                    INNER JOIN servicedocument.PEDIDOS PED ON(PED.CNPJ_CLIENTE = PESS.CHAVECNPJ)
                    WHERE PED.ID_PEDIDO = %s 
                    LIMIT 1 """

        sql = sql
        qry = self.conexao.execute_query_to_dict(sql, [id_pedido])
        return qry

    def obterEnderecoCliente(self, id_cliente):
        if id_cliente == IsEmpty or None:
            return None

        sql = """SELECT 
                E.TIPOLOGRADOURO,
                E.LOGRADOURO,
                E.NUMERO,
                E.COMPLEMENTO,
                E.BAIRRO,
                E.IBGE 	AS CODIGOMUNICIPIO,
                (SELECT M.NOME FROM NS.MUNICIPIOS M WHERE M.IBGE = E.IBGE) AS MUNICIPIO,
                COALESCE(E.UF, E.UFEXTERIOR) AS UF,
                E.CEP,
                E.PAIS,
                (SELECT P.NOME FROM NS.PAISES P WHERE P.PAIS = E.PAIS) AS PAISNOME,
                NULL               	AS TELEFONE,
                NULL               	AS REFERENCIA
            FROM NS.ENDERECOS E
            WHERE E.ID_PESSOA = %s
            AND E.TIPOENDERECO = 0
            LIMIT 1"""

        qry = self.conexao.execute_query_to_dict(sql, [id_cliente])
        if len(qry) == 0:
            return None
        else:
            return qry

    def obterEnderecoPrestacao(self, id_pedido):
        if id_pedido == IsEmpty or None:
            return None

        sql = """SELECT 
                tipo_logradouro,
                logradouro,
                numero,
                complemento,
                cep,
                bairro,
                codigo_municipio,
                nome_municipio,
                codigo_pais,
                uf,
                telefone,
                referencia,
                nome_pais
            FROM servicedocument.enderecos
            WHERE id_pedido = %s
            and tipo_endereco = 1
            LIMIT 1"""

        qry = self.conexao.execute_query_to_dict(sql, [id_pedido])
        if len(qry) == 0:
            return None
        else:
            return qry[0]

    def obterEnderecoEntrega(self, id_pedido):
        if id_pedido == IsEmpty or None:
            return None

        sql = """SELECT 
                tipo_logradouro,
                logradouro,
                numero,
                complemento,
                cep,
                bairro,
                codigo_municipio,
                nome_municipio,
                codigo_pais,
                uf
            FROM servicedocument.enderecos
            WHERE id_pedido = %s
            and tipo_endereco = 0
            LIMIT 1"""

        qry = self.conexao.execute_query_to_dict(sql, [id_pedido])
        if len(qry) == 0:
            return None
        else:
            return qry[0]

    def obterFormasPagamentos(self, id_pedido):
        sql = """SELECT
                f.cod_tipopagamento,
                (SELECT a.codigo 
                        FROM ns.formaspagamentos a
                        WHERE lower(a.descricao) = lower(f.cod_tipopagamento)
                        LIMIT 1
                ) AS tipoformapagamento,
                valor_parcela,
                dt_vencimento,
                numero
                FROM servicedocument.pagamentos f
                WHERE f.id_pedido = %s
                order by numero ASC, dt_vencimento"""

        sql = sql
        return self.conexao.execute_query_to_dict(sql, [id_pedido])


class DAO:
    def __init__(self, conexao_banco: DBAdapter = None):

        self.conexao = conexao_banco
        self.t_pedidos = Tpedidos(conexao_banco)
        self.registraLog = registra_log(conexao_banco)
        self.xml_serviceDocument = xml_service_document(conexao_banco)
        self.dir_instalacao_erp = dir_instalacao_erp(conexao_banco)

    def obterDocumentosEnviados(self, identificador, situacoes):
        query_situacao = ""
        if situacoes.count == 1:
            query_situacao = situacoes[0]
        else:
            for situacao in situacoes:
                if query_situacao == "":
                    query_situacao = str(situacao.value)
                else:
                    query_situacao = query_situacao + "," + str(situacao.value)
        # busca todas as mensagens referentes ao documento xml (identificador)
        # que ainda nao foram importadas para o log de execucao do job
        sql = (
            """select df.numero, df.serie, d.* 
            FROM servicedocument.documentos d
            LEFT JOIN ns.df_docfis df ON (df.id = d.id_docfis)
            where d.identificador::int = %s
            and d.status in ("""
            + query_situacao
            + """)
            and d.excluido = FALSE
            AND NOT EXISTS (SELECT le.id_doc_service_msg 
            				FROM servicedocument.log_execucaojob le 
            				WHERE 
            				le.id_doc_service_msg = d.documento
            				)
            ORDER BY d.datahora_inclusao DESC"""
        )

        return self.conexao.execute_query_to_dict(sql, [identificador])

    def cfopValido(self, num_cfop: str):
        if num_cfop.strip() == IsEmpty or None:
            return False

        sql = """SELECT 1 AS CFOP_OK FROM ns.cfop c 
                WHERE c.cfop = """ + quotedString(
            num_cfop
        )

        # sql = """SELECT 1 AS CFOP_OK
        #         FROM ns.cfop c
        #         WHERE
        #         c.cfop LIKE '51%' AND
        #         NOT c.cfop LIKE '%0'
        #         AND c.tipo = 0
        #         AND c.cfop = """ + quotedString(num_cfop)

        qry = self.conexao.execute_query_to_dict(sql)
        if len(qry) == 0:
            return False
        else:
            return (qry[0]["cfop_ok"] != None) and (qry[0]["cfop_ok"] == 1)

    def localEstoqueValido(self, codigo: str = None, idEstabecimento: str = None):
        if (codigo != IsEmpty) and (idEstabecimento != IsEmpty):
            sql = "SELECT 1 AS CODIGO FROM estoque.locaisdeestoques e WHERE e.codigo = %s and e.estabelecimento = %s Limit 1"
            qry = self.conexao.execute_query_to_dict(sql, [codigo, idEstabecimento])
            if len(qry) == 0 or None:
                return False
            else:
                return (qry[0]["codigo"] != None) and (qry[0]["codigo"] == 1)
        else:
            return False

    def ObterProximoNumNotaFiscal(
        self, a_tipodoc: str, a_serie: str, a_estabelecimento: str
    ):
        sql = "Select * from getproximonumeroseriedoc({1}, {2}, {3})"
        qry = self.conexao.execute_query_to_dict(
            sql, [a_tipodoc, a_serie, a_estabelecimento]
        )
        return qry["getproximonumeroseriedoc"]
