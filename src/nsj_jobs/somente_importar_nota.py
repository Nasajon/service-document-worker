
import traceback
from nsj_jobs.resources.envconfig import EnvConfig
from nsj_jobs.service_document_cmd import ServiceDocumentCMD
from nsj_jobs.dao import DAO, Status, StatusDocumento, Tp_Operacao, tipoMsg, Tpedido
from nsj_jobs.resources.job_command import JobCommand
from nsj_jobs.resources.create_nota import montar_LayoutCalculaImpostos
from datetime import datetime, timedelta


class ImportacaoNota(JobCommand):
    def __init__(self):
        self.banco = None
        self.nota_fiscal = None
        self.registro_execucao = None
        self.maximoTentativasConfig = int(
            EnvConfig.instance().maximo_tentativas)
        self.intervalo_tentativas = (24*60) / (self.maximoTentativasConfig-1)

    def execute(self, entrada: dict, job, db, log, registro_execucao):

        try:
            self.registro_execucao = registro_execucao
            self.banco = DAO(db)
            registro_execucao.informativo(
                'Obtendo o caminho configurado para salvar os arquivos xml.')
            path_EnvioNFSE = self.banco.xml_serviceDocument.obterCaminhoArquivo(
                82, 0)
            path_EnvioNFE = self.banco.xml_serviceDocument.obterCaminhoArquivo(
                70, 0)

            path_CancelamentoNFSE = self.banco.xml_serviceDocument.obterCaminhoArquivo(
                86, 0)
            path_CancelamentoNFE = self.banco.xml_serviceDocument.obterCaminhoArquivo(
                74, 0)

            # obtem os pedidos que ja foram processados (xml criados) da tabela de controle
            # obtem os registros de envios de xml em documentos (servicedocument.documentos)
            # atualiza a tabela de pedidos, de acordo com os status do envio do xml em documentos

            erros_documento = [StatusDocumento.sdcErroProcessamento.value,
                               StatusDocumento.sdcErroEmissao.value,
                               StatusDocumento.sdcErroConsulta.value,
                               StatusDocumento.sdcRespondidoComFalha.value]
            documento_situacoes = [StatusDocumento.sdcTransmitido,
                                    StatusDocumento.sdcImportado,
                                    StatusDocumento.sdcErroProcessamento,
                                    StatusDocumento.sdcErroEmissao,
                                    StatusDocumento.sdcErroConsulta,
                                    StatusDocumento.sdcRespondidoComFalha]
            # Aberto = 0 | Reemitir = 3 | Cancelamento_Fiscal = 5
            situacoes = [Status.Aberto, Status.Reemitir,
                         Status.Cancelamento_Fiscal]

            registro_execucao.informativo(
                'Obtendo pedidos que ja foram processados (xml criados) da tabela de controle.')
            pedidos = self.banco.t_pedidos.obterPedidos_Processados(situacoes)
            t_pedido = Tpedido(db)

            registro_execucao.informativo(
                'Obtendo os registros de envios de xml em documentos (servicedocument.documentos).')
            for pedido in pedidos:
                var_id_pedido = pedido.get('id_pedido')
                var_identificador = int(pedido.get('num_pedido'))
                documentos = self.banco.obterDocumentosEnviados(
                    var_identificador, documento_situacoes)
                registro_execucao.informativo(
                    f'Obtendo os registros do pedido de id: {var_id_pedido} e número: {var_identificador}.')

                if len(documentos) != 0:
                    t_pedido.pedido = pedido

                    registro_execucao.informativo(
                        'Verificando os registros de logs criados para o documento')
                    for documento in documentos:
                        if (int(documento.get('status')) == StatusDocumento.sdcTransmitido.value):
                            # sucesso! Status = 2
                            statusDocto = documento.get('status')
                            statusAtual = pedido.get('status')
                            novoStatus = self.novoStatus(
                                statusDocto, statusAtual)

                            if (novoStatus is None) or (novoStatus == statusAtual):
                                registro_execucao.informativo(
                                    f'Id do pedido: {var_id_pedido}. Novo status inválido: {novoStatus}')
                                self.banco.registraLog.mensagem(var_id_pedido, 'Novo Status inválido: ' + str(novoStatus),
                                                                tipoMsg.inconsistencia, documento.get('documento'))
                                continue
                            else:
                                registro_execucao.informativo(
                                    'Atualizando a tabela de pedidos, de acordo com os status do envio do xml em documentos.')

                                t_pedido.camposAtualizar['status'] = str(
                                    novoStatus)
                                t_pedido.camposAtualizar['chave_de_acesso'] = documento.get(
                                    'chave_emissao')
                                t_pedido.camposAtualizar['numero_nf'] = documento.get(
                                    'numero')
                                t_pedido.camposAtualizar['serie_nf'] = documento.get(
                                    'serie')
                                t_pedido.camposAtualizar['id_docfis'] = documento.get(
                                    'id_docfis')
                                t_pedido.camposAtualizar['mensagem'] = documento.get(
                                    'mensagem_retorno')
                                t_pedido.camposAtualizar['id_doc_serv_msg'] = documento.get(
                                    'documento')
                                t_pedido.updatePedido()
                                break
                        elif int(documento.get('status')) == StatusDocumento.sdcImportado.value and not pedido['emitir_nota']:
                                registro_execucao.informativo(
                                    'Atualizando a tabela de pedidos.')

                                t_pedido.camposAtualizar['status'] = str(
                                    Status.Emitido.value)
                                t_pedido.camposAtualizar['chave_de_acesso'] = documento.get(
                                    'chave_emissao')
                                t_pedido.camposAtualizar['numero_nf'] = documento.get(
                                    'numero')
                                t_pedido.camposAtualizar['serie_nf'] = documento.get(
                                    'serie')
                                t_pedido.camposAtualizar['id_docfis'] = documento.get(
                                    'id_docfis')
                                t_pedido.camposAtualizar['mensagem'] = documento.get(
                                    'mensagem_retorno')
                                t_pedido.camposAtualizar['id_doc_serv_msg'] = documento.get(
                                    'documento')
                                t_pedido.updatePedido()
                                break
                        elif int(documento.get('status')) in erros_documento:
                            # Se gerou registrou no docfis mas está com erro, rejeita o pedido.
                            if documento.get('id_docfis') is not None:
                                t_pedido.updateSituacao(Status.Rejeitado.value)
                                strAviso = f"Erro ao tratar o pedido {var_identificador} no ServiceDocument. {documento.get('mensagem_retorno')}"
                                registro_execucao.erro_execucao(strAviso)
                                self.banco.registraLog.mensagem(
                                    var_id_pedido, strAviso, tipoMsg.serviceDocument, documento.get('documento'))
                                break
                            else:
                                strAviso = f"Erro ao tratar o pedido {var_identificador} no ServiceDocument. {documento.get('mensagem_retorno')}"
                                registro_execucao.erro_execucao(strAviso)
                                self.banco.registraLog.mensagem(
                                    var_id_pedido, strAviso, tipoMsg.serviceDocument)

                                # Verifica se deve tentar de novo. Se não puder tentar de novo, rejeita
                                if not self.iterarTentativaParaServiceDocument(t_pedido, documento):
                                    t_pedido.updateSituacao(
                                        Status.Rejeitado.value)

                                break

                # fim loop documento enviados
            # fim loop pedidos.

            # inicia o loop para criacao dos arquivos XML
            # obtem os pedidos que ainda nao foram processados: (processado = False , emitir = True)

            registro_execucao.informativo(
                'Obtendo os pedidos que ainda não foram processados.')
            pedidos = self.banco.t_pedidos.obterPedidos(
                [Status.Aberto], False, True)
            pedidos.extend(self.banco.t_pedidos.obterPedidos(
                [Status.Reemitir, Status.Cancelamento_Fiscal], False, False))

            total_reg = len(pedidos)
            total_proc = 0
            tot_falha = 0

            registro_execucao.informativo('Criando os arquivos XML.')
            for pedido in pedidos:

                if pedido['status'] == Status.Reemitir.value:
                    t_pedido = Tpedido(db)
                    t_pedido.pedido = pedido
                    tentativaAdicionalAtual = t_pedido.pedido['tentativas_adicionais'] + 1
                    # Verifica se tem tentativas adicionais
                    if tentativaAdicionalAtual < self.maximoTentativasConfig:
                        # Calcula a partir de quando deve ser a próxima tentativa
                        proximaTentativa = t_pedido.pedido['primeira_tentativa'] + timedelta(
                            minutes=tentativaAdicionalAtual*self.intervalo_tentativas)
                        if datetime.now() < proximaTentativa:
                            # Remover quantidade para não aparecer no total no log, para evitar confusão
                            total_reg -= 1
                            continue
                    else:
                        # Se não tiver mais tentivas, rejeita
                        t_pedido.updateSituacao(Status.Rejeitado.value)
                        # Remover quantidade para não aparecer no total no log, para evitar confusão
                        total_reg -= 1
                        continue

                strNum_nf = '00000'
                var_id_pedido = pedido['id_pedido']
                var_num_pedido = pedido['num_pedido']
                registro_execucao.informativo(
                    'Processando o pedido ' + str(var_num_pedido))

                t_pedido.obterPedidoId(var_id_pedido)
                dados_ok = self.validarDados(t_pedido)
                if not dados_ok:
                    if t_pedido.pedido['primeira_tentativa']:
                        t_pedido.atualizarTentativa(t_pedido.pedido['primeira_tentativa'], datetime.now(
                        ), t_pedido.pedido['tentativas_adicionais']+1)
                    else:
                        t_pedido.registrarPrimeiraTentativaParaReemissao()
                    tot_falha = tot_falha + 1
                    continue

                if int(pedido['status']) == Status.Cancelamento_Fiscal.value:
                    pathdefault = path_CancelamentoNFSE if t_pedido.pedido[
                        'tipo_nota'] == 'NFSE' else path_CancelamentoNFE
                    s_msg = 'Diretório de cancelamento para salvar o arquivo xml não foi definido no Admin.'
                else:
                    pathdefault = path_EnvioNFSE if t_pedido.pedido[
                        'tipo_nota'] == 'NFSE' else path_EnvioNFE
                    s_msg = 'Diretório de envio para salvar o arquivo xml não foi definido no Admin.'

                registro_execucao.informativo(
                    'Iniciando a criacao do arquivo xml...')

                try:
                    if pathdefault is None:
                        registro_execucao.informativo(s_msg)
                        raise Exception(s_msg)

                    montar_LayoutCalculaImpostos(
                        t_pedido, pathdefault, strNum_nf)

                    t_pedido.updatePedidoProcessado(var_id_pedido)
                    strAviso = 'Criado arquivo xml do pedido ' + \
                        str(var_num_pedido)
                    registro_execucao.informativo(
                        f'Id do pedido: {var_id_pedido}. {strAviso}')
                    self.banco.registraLog.mensagem(
                        var_id_pedido, strAviso, tipoMsg.sucesso)
                    total_proc = total_proc + 1
                except Exception as e:
                    if t_pedido.pedido['primeira_tentativa']:
                        t_pedido.atualizarTentativa(t_pedido.pedido['primeira_tentativa'], datetime.now(
                        ), t_pedido.pedido['tentativas_adicionais']+1)
                    else:
                        t_pedido.registrarPrimeiraTentativaParaReemissao()
                    strAviso = f'Erro ao criar arquivo xml para o pedido {var_num_pedido}. Erro: {e}'
                    registro_execucao.erro_execucao(strAviso)
                    self.banco.registraLog.mensagem(
                        var_id_pedido, strAviso, tipoMsg.inconsistencia)
                    tot_falha = tot_falha + 1

            registro_execucao.informativo(
                f"Total Lidos: {total_reg} | Total Processados:{total_proc}, Total Falhas:{tot_falha}")

            # Execução do ServiceDocument
            if entrada['env'] == 'docker':
                dirInstalacaoERP = "C:\\Nasajon Sistemas\\Integratto2\\"
            elif entrada['env'] == 'jobmanager':
                dirInstalacaoERP = self.banco.dir_instalacao_erp.obterDiretorioInstalacao()

            serviceDocument = ServiceDocumentCMD(
                dirInstalacaoERP, entrada, 'SOMENTE_IMPORTACAO')
            serviceDocument.executar()

        except Exception as e:
            mensagem = "Erro inesperado: {0}".format(str(e))
            registro_execucao.exception_execucao(mensagem)

    # Reagendar um pedido para ser reprocessado pelo worker. Retorna se ainda tem tentativas disponíveis ou não
    def iterarTentativaParaServiceDocument(self, t_pedido: Tpedido, documento):
        # Retorna True se houverem tentativas restantes antes de falhar, False do contrário
        dataHoraPrimeiraTentativa = t_pedido.pedido['primeira_tentativa']
        tentativasAdicionais = t_pedido.pedido['tentativas_adicionais']

        # Quando não houverem tentativas adicionais
        if self.maximoTentativasConfig == 1:
            t_pedido.atualizarTentativa(documento.get(
                'datahora_inclusao'), documento.get('datahora_inclusao'))
            return False

        tentativaAdicionalAtual = tentativasAdicionais + 1
        if tentativaAdicionalAtual < self.maximoTentativasConfig:

            # Caso seja a primeira retentativa
            if dataHoraPrimeiraTentativa is None:
                dataHoraPrimeiraTentativa = documento.get('datahora_inclusao')
                t_pedido.atualizarTentativa(documento.get(
                    'datahora_inclusao'), documento.get('datahora_inclusao'))

            # Calcula a partir de quando deve ser a próxima tentativa
            proximaTentativa = dataHoraPrimeiraTentativa + \
                timedelta(minutes=tentativaAdicionalAtual *
                          self.intervalo_tentativas)
            if datetime.now() > proximaTentativa:
                t_pedido.atualizarTentativa(
                    dataHoraPrimeiraTentativa, documento.get('datahora_inclusao'), tentativaAdicionalAtual)
            return True

        return False

    def validarDados(self, a_pedido: Tpedido):
        b_dados_validos = False
        strPedido = str(a_pedido.pedido['id_pedido'])
        num_pedido = a_pedido.pedido['num_pedido']

        if (a_pedido.lstCliente is None):
            strAviso = f"""Erro ao criar arquivo xml para o pedido {num_pedido}. 
                        Cliente não encontrado para o CNPJ/CPF informado: {a_pedido.pedido['cnpj_cliente']}"""
            self.registro_execucao.informativo(strAviso)
            self.banco.registraLog.mensagem(
                strPedido, strAviso, tipoMsg.inconsistencia)
            return False

        if (a_pedido.lstEndCliente is None):
            strAviso = f'Erro ao criar arquivo xml para o pedido {num_pedido}. Endereço do Cliente não retornou registros!'
            self.registro_execucao.informativo(strAviso)
            self.banco.registraLog.mensagem(
                strPedido, strAviso, tipoMsg.inconsistencia)
            return False

        if (a_pedido.lstFormaPagamento is None):
            strAviso = f'Erro ao criar arquivo xml para o pedido {num_pedido}.Forma de Pagamento não retornou registros!'
            self.registro_execucao.informativo(strAviso)
            self.banco.registraLog.mensagem(
                strPedido, strAviso, tipoMsg.inconsistencia)
            return False

        if (a_pedido.lstEstabelecimento is None):
            strAviso = f"""Erro ao criar arquivo xml para o pedido {num_pedido}.
                        Estabelecimento não encontrado para CNPJ Informado: {a_pedido.pedido['cnpj_estabelecimento']}"""
            self.registro_execucao.informativo(strAviso)
            self.banco.registraLog.mensagem(
                strPedido, strAviso, tipoMsg.inconsistencia)
            return False
        else:
            var_id_Estab = str(
                a_pedido.lstEstabelecimento[0]['id_estabelecimento'])

        strmsg = 'Valor inválido informado para o campo {} . [ {} ] = {}'
        erroLista = []
        var_loc_estoq = str(a_pedido.pedido['localestoque'])

        try:
            self.registro_execucao.informativo('Validando dados do pedido.')
            # validar dados do pedido:
            if a_pedido.pedido["tipo_nota"] in ['NFE'] and a_pedido.pedido['id_operacao'] == '':
                strAviso = strmsg.format(
                    'Código da Operação', 'COD_OPERACAO', 'vazio')
                erroLista.append(strAviso)

            if a_pedido.pedido["tipo_nota"] in ['NFE'] and a_pedido.pedido['tp_operacao'] not in [item.value for item in Tp_Operacao]:
                strAviso = strmsg.format(
                    'Tipo da Operação', 'TP_OPERACAO', a_pedido.pedido['tp_operacao'])
                erroLista.append(strAviso)

            if a_pedido.pedido["tipo_nota"] in ['NFE'] and a_pedido.pedido['tipodocumento'] != 55:
                strAviso = strmsg.format(
                    'Tipo de documento', 'TIPODOCUMENTO', a_pedido.pedido['tipodocumento'])
                erroLista.append(strAviso)

            if (var_loc_estoq != '') and var_loc_estoq is not None:
                if a_pedido.pedido["tipo_nota"] in ['NFE'] and not self.banco.localEstoqueValido(var_loc_estoq, var_id_Estab):
                    strAviso = strmsg.format(
                        'Local de Estoque', 'LOCALESTOQUE', var_loc_estoq)
                    erroLista.append(strAviso)
            else:
                strAviso = strmsg.format(
                    'Local de Estoque', 'LOCALESTOQUE', 'vazio')
                erroLista.append(strAviso)

            date_time_str = str(a_pedido.pedido['dt_emissao'])
            if (date_time_str == '') and (date_time_str is None):
                erroLista.append('Data de Emissão não preenchida')

            # validar dados do cliente:
            self.registro_execucao.informativo('Validando dados do cliente.')
            if (a_pedido.lstCliente is None or len(a_pedido.lstCliente) == 0):
                erroLista.append(
                    'Cliente não encontrado com o CNPJ/CPF informado: ' + str(a_pedido.pedido['cnpj_cliente']))

            self.registro_execucao.informativo('Validando dados do produto.')
            # validar dados do produto (itens do pedido):
            if a_pedido.pedido["tipo_nota"] in ['NFE']:
                for produto in a_pedido.lstProdutos:

                    if ((produto.get('sem_saldo') == 1) and (produto.get('mensagem_erro') != '')):
                        erroLista.append(produto.get('mensagem_erro'))

                    if produto.get('prod_nao_existe') == 1:
                        strAviso = strmsg.format(
                            'Código do Produto', 'COD_PRODUTO', produto.get('cod_produto'))
                        erroLista.append(strAviso)

                    if 'USO_CONSUMO' in produto.get('cod_produto'):
                        erroLista.append(f'Produto {produto.get("cod_produto")} de uso e consumo não pode fazer parte do pedido.')

                    var_loc_estoq = str(produto.get('localestoque'))

                    if (var_loc_estoq != '') and (var_loc_estoq is not None):
                        if not self.banco.localEstoqueValido(var_loc_estoq, var_id_Estab):
                            erroLista.append(
                                'Valor inválido informado para o campo [LOCALESTOQUE] no item.')
                    else:
                        erroLista.append(
                            'Valor não foi informado para o campo [LOCALESTOQUE] no item.')

                    if (produto.get('documentoreferenciado_chave') is not None) and (produto.get('documentoreferenciado_chave') != ''):
                        if (len(produto.get('documentoreferenciado_chave')) < 44):
                            strAviso = strmsg.format('Documento referenciado', 'DOCUMENTOREFERENCIADO_CHAVE', produto.get(
                                'documentoreferenciado_chave'))
                            erroLista.append(strAviso)

            for pagamento in a_pedido.lstFormaPagamento:
                if (pagamento.get('tipoformapagamento') is None) or (pagamento.get('tipoformapagamento') == ''):
                    strAviso = strmsg.format(
                        'Tipo de Pagamento', 'TIPOFORMAPAGAMENTO', pagamento.get('tipoformapagamento'))
                    erroLista.append(strAviso)

            if (len(erroLista) == 0):
                b_dados_validos = True
            else:
                self.listarErros(strPedido, erroLista,
                                 tipoMsg.inconsistencia, num_pedido)

        except Exception:
            self.listarErros(strPedido, erroLista,
                             tipoMsg.inconsistencia, num_pedido)
            return False

        return b_dados_validos

    def listarErros(self, id, lista, a_tipo: tipoMsg, num_pedido):
        for err in lista:
            mensagem = f"Erro ao criar arquivo xml para o pedido {num_pedido}. {err}"
            self.banco.registraLog.mensagem(id, mensagem, a_tipo)
            self.registro_execucao.erro_execucao(mensagem)

    def novoStatus(self, status_Doc: int, statusAtualPedido: int):

        var_resultado = statusAtualPedido

        if statusAtualPedido in [Status.Rejeitado.value, Status.Aberto.value,
                                 Status.Reemitir.value, Status.Cancelamento_Fiscal.value]:
            # nao altera o status do pedido se a situacao atual for: Aberto, Reemissao, cancelamento fiscal.
            # e se houve a emissao do xml pelo servicedocument com sucesso!
            if status_Doc == StatusDocumento.sdcTransmitido.value:
                if statusAtualPedido != Status.Cancelamento_Fiscal.value:
                    var_resultado = Status.Emitido.value     # valor = 1
                else:
                    var_resultado = Status.Cancelado.value   # valor = 6
            else:
                # se ocorreu erro na transmissao do xml, a situacao deve alterar para falha (rejeitado)
                if status_Doc in [StatusDocumento.sdcErroProcessamento.value,
                                  StatusDocumento.sdcErroEmissao.value,
                                  StatusDocumento.sdcRespondidoComFalha.value]:
                    var_resultado = Status.Rejeitado         # valor = 3 -- marcar como uma falha
                else:
                    # não faz alteracao do status, retorna status atual
                    var_resultado = statusAtualPedido

        return var_resultado

    def formataNumZeros(self, quant_zeros: int, numero: int) -> str:
        sfmt = '%0{}d'.format(quant_zeros)
        num_zeros = sfmt % (numero,)
        return num_zeros


# Para teste
if __name__ == '__main__':
    ImportacaoNota().execute_cmd({'env': 'docker'})
