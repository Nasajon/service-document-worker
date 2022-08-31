
import traceback
from nsj_jobs.resources.envconfig import EnvConfig
from nsj_jobs.resources.log import Log
from nsj_jobs.service_document_cmd import ServiceDocumentCMD
from nsj_jobs.dao import DAO, Status, StatusDocumento, Tp_Operacao, tipoMsg, Tpedidos, Tpedido
from nsj_jobs.resources.job_command import JobCommand
from nsj_jobs.resources.create_nota import montar_LayoutCalculaImpostos
from datetime import date
from datetime import datetime, timedelta
import json # utilizado em modo debug


class EmissaoNota(JobCommand):
    def __init__(self):
        self.banco = None
        self.nota_fiscal = None
        self.registro_execucao = None

    def execute(self, entrada: dict, job, db, log, registro_execucao):
       
        try: 
            self.registro_execucao = registro_execucao
            self.banco = DAO(db)
            registro_execucao.informativo('Obtendo o caminho configurado para salvar os arquivos xml.')
            path_Envio = self.banco.xml_serviceDocument.obterCaminhoArquivo(70, 0)
            if path_Envio is None:
                registro_execucao.informativo('Diretório de envio para salvar o arquivo xml não foi definido no Admin.')
                exit
            
            path_Cancelamento = self.banco.xml_serviceDocument.obterCaminhoArquivo(74, 0)
            if path_Cancelamento is None:
                registro_execucao.informativo('Diretório de cancelamento para salvar o arquivo xml não foi definido no Admin.')
                exit
            
            # obtem os pedidos que ja foram processados (xml criados) da tabela de controle
            # obtem os registros de envios de xml em documentos (servicedocument.documentos)
            # atualiza a tabela de pedidos, de acordo com os status do envio do xml em documentos

            # Aberto = 0 | Rejeitado = 2 | Reemitir = 3 | Cancelamento_Fiscal = 5
            situacoes = [Status.Aberto, Status.Rejeitado, Status.Reemitir, Status.Cancelamento_Fiscal]

            erros_documento = [ StatusDocumento.sdcErroProcessamento.value,
                                StatusDocumento.sdcErroEmissao.value,
                                StatusDocumento.sdcErroConsulta.value,
                                StatusDocumento.sdcRespondidoComFalha.value]             
            registro_execucao.informativo('Obtendo pedidos que ja foram processados (xml criados) da tabela de controle.')
            pedidos = self.banco.t_pedidos.obterPedidos_Processados(situacoes)
            t_pedido = Tpedido(db)

            registro_execucao.informativo('Obtendo os registros de envios de xml em documentos (servicedocument.documentos).')
            for pedido in pedidos:
                falhou = False
                var_id_pedido = pedido.get('id_pedido')
                var_identificador = int(pedido.get('num_pedido') )
                documentos = self.banco.obterDocumentosEnviados(var_identificador)
                registro_execucao.informativo(f'Obtendo os registros do pedido de id: {var_id_pedido} e número: {var_identificador}.')
                
                if len(documentos) == 0:
                    
                    registro_execucao.informativo(f'Id do Pedido: {var_id_pedido}. Documento não encontrado para o identificador: {var_identificador}')
                    self.banco.registraLog.mensagem(
                        var_id_pedido, 
                        'Documento não encontrado para o identificador: ' + str(var_identificador), 
                        tipoMsg.serviceDocument)
                else:
                    t_pedido.lstPedido = pedido
                    
                    registro_execucao.informativo('Verificando os registros de logs criados para o documento')
                    for documento in documentos:
                        if ( int(documento.get('status') ) == StatusDocumento.sdcTransmitido.value ):
                            if not(documento.get('chave_emissao') is None): 
                                # sucesso! Status = 2
                                statusDocto = documento.get('status')
                                statusAtual = pedido.get('status')
                                novoStatus  = self.novoStatus(statusDocto, statusAtual)

                                if (novoStatus is None) or (novoStatus == statusAtual):
                                    registro_execucao.informativo(f'Id do pedido: {var_id_pedido}. Novo status inválido: {novoStatus}')
                                    self.banco.registraLog.mensagem(var_id_pedido, 'Novo Status inválido: ' + str(novoStatus) , 
                                            tipoMsg.inconsistencia, documento.get('documento') )
                                    continue 
                                else:
                                    registro_execucao.informativo('Atualizando a tabela de pedidos, de acordo com os status do envio do xml em documentos.')
                                    
                                    t_pedido.camposAtualizar['status'] = str(novoStatus)
                                    t_pedido.camposAtualizar['chave_de_acesso'] = documento.get('chave_emissao')
                                    t_pedido.camposAtualizar['numero_nf'] = documento.get('numero')
                                    t_pedido.camposAtualizar['id_docfis'] = documento.get('id_docfis')
                                    t_pedido.camposAtualizar['mensagem']  = documento.get('mensagem_retorno')
                                    t_pedido.camposAtualizar['id_doc_serv_msg'] = documento.get('documento')
                                    t_pedido.updatePedido()
                                    falhou = False
                                    break                    
                        else:
                            erro_falha = ( int(documento.get('status') ) in erros_documento) # erro ou falha
                            if not self.iterarTentativa(t_pedido, documento) and erro_falha:
                                falhou = True
                                msg_retorno = documento.get('mensagem_retorno')
                                registro_execucao.informativo(f'Id do pedido: {var_id_pedido}. {msg_retorno}')
                                self.banco.registraLog.mensagem(var_id_pedido, msg_retorno, 
                                    tipoMsg.serviceDocument, documento.get('documento') )
                    
                    if falhou:
                        t_pedido.updateSituacao(Status.Rejeitado.value) #atualiza o status para 2

                # fim loop documento enviados
            # fim loop pedidos.

            # inicia o loop para criacao dos arquivos XML
            # obtem os pedidos que ainda nao foram processados: (processado = False , emitir = True)
            situacoes.clear
            situacoes = [Status.Aberto, Status.Reemitir, Status.Cancelamento_Fiscal]
     
            registro_execucao.informativo('Obtendo os pedidos que ainda não foram processados.')
            pedidos = self.banco.t_pedidos.obterPedidos(situacoes, False)

            total_reg  = len(pedidos)
            total_proc = 0
            tot_falha  = 0
            
            registro_execucao.informativo('Criando os arquivos XML.')
            for pedido in pedidos:
                strNum_nf = '00000'
                var_id_pedido  = pedido['id_pedido']
                var_num_pedido = pedido['num_pedido']

                t_pedido.obterPedidoId( var_id_pedido )
                dados_ok = self.validarDados(t_pedido)
                if not dados_ok:
                    tot_falha = tot_falha + 1
                    continue

                # OBTEM O NUMERO DA NOTA FISCAL: (nao utilizado)     
                # tipoDoc = str( t_pedido.lstPedido.get('tipodocumento') )
                # numSerie = '{serie_nf}{subserie}'.format(serie_nf = t_pedido.lstPedido.get('serie_nf'), subserie = t_pedido.lstPedido.get('subserie'))
                # strNum_nf = self.banco.ObterProximoNumNotaFiscal(tipoDoc, numSerie, str(t_pedido.lstPedido.id_estabecimento) )

                if int(pedido['status']) == Status.Cancelamento_Fiscal.value:
                    pathdefault = path_Cancelamento
                else:
                    pathdefault = path_Envio

                registro_execucao.informativo('Iniciando a criacao do arquivo xml...')
                arquivo = montar_LayoutCalculaImpostos(t_pedido, pathdefault, strNum_nf)

                if (arquivo != ''):
                    t_pedido.updatePedidoProcessado( var_id_pedido )
                    strAviso = 'Criado arquivo xml do pedido ' + str(var_num_pedido) 
                    registro_execucao.informativo(f'Id do pedido: {var_id_pedido}. {strAviso}')
                    self.banco.registraLog.mensagem( var_id_pedido, strAviso, tipoMsg.sucesso)
                    total_proc = total_proc  + 1
                else:
                    strAviso = 'Erro ao criar arquivo xml para o pedido ' + str(var_num_pedido)
                    registro_execucao.erro_execucao(f'Id do pedido: {var_id_pedido}. {strAviso}')
                    self.banco.registraLog.mensagem(var_id_pedido, strAviso, tipoMsg.inconsistencia)

                ## registro_execucao.informativo(strAviso)

            ## print("Total Lidos: {0} | Total Processados:{1}, Total Falhas:{2}".format(str(total_reg), str(total_proc), str(tot_falha) ) )

            # Execução do ServiceDocument
            # dirInstalacaoERP = self.banco.dir_instalacao_erp.obterDiretorioInstalacao()
            dirInstalacaoERP = "C:\\Nasajon Sistemas\\Integratto2\\"
            serviceDocument = ServiceDocumentCMD(dirInstalacaoERP)
            serviceDocument.executar()


        except Exception as e:
            mensagem = "Erro inesperado: {0}".format(str(e))
            mensagem += "\n".join(traceback.format_exception(e))
            registro_execucao.exception_execucao(mensagem)
            exit;

    def iterarTentativa(self, t_pedido: Tpedido, documento):
        # Retorna True se houverem tentativas restantes antes de falhar, False do contrário
        dataHoraUltimaTentativaPedido = t_pedido.lstPedido['ultima_tentativa']
        dataHoraUltimaTentativaDocumento = documento.get('datahora_inclusao')
        dataHoraPrimeiraTentativa = t_pedido.lstPedido['primeira_tentativa']
        tentativasAdicionais = t_pedido.lstPedido['tentativas_adicionais']
        maximoTentativasConfig = int(EnvConfig.instance().maximo_tentativas)
        formatoDataHora = "%Y-%m-%d %H:%M:%S.%f"

        # Quando não houverem tentativas adicionais
        if maximoTentativasConfig == 1:
            if tentativasAdicionais == 0:
                t_pedido.atualizarTentativa(dataHoraUltimaTentativaDocumento, dataHoraUltimaTentativaDocumento)
            return False
        
        tentativaAdicionalAtual = tentativasAdicionais + 1
        if tentativaAdicionalAtual < maximoTentativasConfig:
            # Primeira tentativa no minuto 0 e a última 24 horas depois
            intervalo_tentativas = (24*60) / (maximoTentativasConfig-1)

            # Caso seja a primeira retentativa
            if dataHoraPrimeiraTentativa is None and dataHoraUltimaTentativaPedido is None:
                dataHoraPrimeiraTentativa = dataHoraUltimaTentativaDocumento
                dataHoraUltimaTentativaPedido = dataHoraUltimaTentativaDocumento
                # TODO atualizar primeira e ultimas tentativas neste momento?
            
            # Calcula a partir de quando deve ser a próxima tentativa
            proximaTentativa = dataHoraPrimeiraTentativa + timedelta(minutes=tentativaAdicionalAtual*intervalo_tentativas)
            if datetime.now() > proximaTentativa:
                t_pedido.atualizarTentativa(dataHoraPrimeiraTentativa, dataHoraUltimaTentativaDocumento, tentativaAdicionalAtual)
            return True

        return False


    def validarDados(self, a_pedido: Tpedido):
        b_dados_validos = False 
        strPedido = str( a_pedido.lstPedido[0]['id_pedido'] )

        strAviso = ''
        if ( a_pedido.lstCliente == None):
            strAviso = 'Cliente não encontrado para o CNPJ/CPF informado: ' + str(a_pedido.lstPedido[0]['cnpj_cliente'])
            self.registro_execucao.atencao(strAviso)
            self.banco.registraLog.mensagem( strPedido, strAviso, tipoMsg.inconsistencia)
            return False

        if ( a_pedido.lstEndCliente == None):
            strAviso = 'Endereço do Cliente não retornou registros!'
            self.registro_execucao.atencao(strAviso)
            self.banco.registraLog.mensagem( strPedido, strAviso, tipoMsg.inconsistencia)
            return False 

        if ( a_pedido.lstFormaPagamento == None):
            strAviso = 'Forma de Pagamento não retornou registros!'
            self.registro_execucao.atencao(strAviso)
            self.banco.registraLog.mensagem( strPedido, strAviso, tipoMsg.inconsistencia)
            return False       
        
        if ( a_pedido.lstEstabelecimento == None):
            strAviso = 'Estabelecimento não encontrado para CNPJ Informado: ' + str(a_pedido.lstPedido[0]['cnpj_estabelecimento'])
            self.registro_execucao.atencao(strAviso)
            self.banco.registraLog.mensagem( strPedido, strAviso, tipoMsg.inconsistencia)
            return False
        else:
            var_id_Estab = str( a_pedido.lstEstabelecimento[0]['id_estabelecimento'] )

        strmsg = 'Valor inválido informado para o campo {} . [ {} ] = {}'
        strAviso = ''
        erroLista = []    
        var_loc_estoq= str( a_pedido.lstPedido[0]['localestoque'] )
      
        try:
            self.registro_execucao.informativo('Validando dados do pedido.')
            # validar dados do pedido:
            if a_pedido.lstPedido[0]['id_operacao'] == '':
               strAviso = strmsg.format('Código da Operação', 'COD_OPERACAO', 'vazio' )
               erroLista.append( strAviso )

            if not a_pedido.lstPedido[0]['tp_operacao'] in [item.value for item in Tp_Operacao]:
               strAviso = strmsg.format('Tipo da Operação', 'TP_OPERACAO', a_pedido.lstPedido[0]['tp_operacao'] )
               erroLista.append( strAviso )
                        
            if (a_pedido.lstPedido[0]['serie_nf'] == '' or None):
                strAviso = strmsg.format('Série da Nota Fiscal', 'SERIE_NF', 'vazio' )
                erroLista.append( strAviso )
                      
            if a_pedido.lstPedido[0]['tipodocumento'] != 55:
                strAviso = strmsg.format('Tipo de documento', 'TIPODOCUMENTO', a_pedido.lstPedido[0]['tipodocumento'] )
                erroLista.append( strAviso )
            
            if ( var_loc_estoq != '') and not( var_loc_estoq == None):
                if not self.banco.localEstoqueValido( var_loc_estoq, var_id_Estab ):
                    strAviso = strmsg.format('Local de Estoque', 'LOCALESTOQUE', var_loc_estoq )
                    erroLista.append( strAviso )
            else:
                strAviso = strmsg.format('Local de Estoque', 'LOCALESTOQUE', 'vazio' )
                erroLista.append( strAviso )

            date_time_str = str(a_pedido.lstPedido[0]['dt_emissao'])
            if (date_time_str != '') and (date_time_str != None):
                date_dt = datetime.strptime(date_time_str, '%Y-%m-%d')
                if date_dt.date() > date.today():
                    erroLista.append('Data de emissão [DT_EMISSAO] maior que a data atual.')
            else:
                strAviso = strmsg.format('Data emissão', 'DT_EMISSAO', date_time_str )
                erroLista.append( strAviso )

            # validar dados do cliente:
            self.registro_execucao.informativo('Validando dados do cliente.')
            if ( a_pedido.lstCliente[0]['id_cliente'] == '' or None):
                erroLista.append('Cliente não encontrado com o CNPJ/CPF informado: ' + str(a_pedido.lstPedido[0]['cnpj_cliente']) )

            self.registro_execucao.informativo('Validando dados do produto.')
            # validar dados do produto (itens do pedido):
            for produto in a_pedido.lstProdutos:
                if produto.get('prod_nao_existe') == 1:
                    strAviso = strmsg.format('Código do Produto', 'COD_PRODUTO', produto.get('cod_produto') )
                    erroLista.append( strAviso )
                
                if not self.banco.cfopValido(produto.get('cfop')):
                    strAviso = strmsg.format('CFOP', 'CFOP', produto.get('cfop') )
                    erroLista.append( strAviso )

                var_loc_estoq = str( produto.get('localestoque') )   

                if (var_loc_estoq != '') and (var_loc_estoq != None):
                    if not self.banco.localEstoqueValido(var_loc_estoq, var_id_Estab ):
                        erroLista.append('Valor inválido informado para o campo [LOCALESTOQUE] no item.')
                else:
                    erroLista.append('Valor não foi informado para o campo [LOCALESTOQUE] no item.')

                if (produto.get('documentoreferenciado_chave') != None) and (produto.get('documentoreferenciado_chave') !='') :
                    if ( len(produto.get('documentoreferenciado_chave') ) < 44 ):
                        strAviso = strmsg.format('Documento referenciado', 'DOCUMENTOREFERENCIADO_CHAVE', produto.get('documentoreferenciado_chave') )
                        erroLista.append( strAviso )
                   
            for pagamento in a_pedido.lstFormaPagamento:
                if (pagamento.get('tipoformapagamento') == None) or (pagamento.get('tipoformapagamento') == ''):
                    strAviso = strmsg.format('Tipo de Pagamento', 'TIPOFORMAPAGAMENTO', pagamento.get('tipoformapagamento') )
                    erroLista.append( strAviso )

            if (len(erroLista) == 0):
                b_dados_validos = True
            else:    
                self.listarErros(strPedido, erroLista, tipoMsg.inconsistencia)
            
        except:
            self.listarErros(strPedido, erroLista, tipoMsg.inconsistencia)
            return False

        return b_dados_validos

    def listarErros(self, id, lista, a_tipo: tipoMsg):
        for err in lista:
            self.banco.registraLog.mensagem( id, err, a_tipo)
            self.registro_execucao.erro(f'Id do pedido:{id}. {err}')

    def novoStatus(self, status_Doc:int, statusAtualPedido:int):
        
        var_resultado = statusAtualPedido
        
        if statusAtualPedido in [ Status.Rejeitado.value, Status.Aberto.value , 
                                  Status.Reemitir.value, Status.Cancelamento_Fiscal.value ]:
            # nao altera o status do pedido se a situacao atual for: Aberto, Reemissao, cancelamento fiscal.
            # e se houve a emissao do xml pelo servicedocument com sucesso!
            if status_Doc == StatusDocumento.sdcTransmitido.value :
                if statusAtualPedido != Status.Cancelamento_Fiscal.value:
                    var_resultado =  Status.Emitido.value     # valor = 1
                else:
                    var_resultado = Status.Cancelado.value   # valor = 6
            else:
                # se ocorreu erro na transmissao do xml, a situacao deve alterar para falha (rejeitado)
                if status_Doc in [StatusDocumento.sdcErroProcessamento.value, 
                                    StatusDocumento.sdcErroEmissao.value,
                                    StatusDocumento.sdcRespondidoComFalha.value]:
                    var_resultado = Status.Rejeitado         # valor = 3 -- marcar como uma falha                 
                else:
                    var_resultado = statusAtualPedido       # não faz alteracao do status, retorna status atual
        
        return var_resultado

    def formataNumZeros(self, quant_zeros: int, numero: int) -> str:
        sfmt = '%0{}d'.format(quant_zeros)
        num_zeros = sfmt % (numero,)
        return num_zeros          

# Para teste
if __name__ == '__main__':
   EmissaoNota().execute_cmd()
