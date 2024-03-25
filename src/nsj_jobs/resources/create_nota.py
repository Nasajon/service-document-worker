
# !/usr/bin/env python
# -*- coding: cp1252 -*-

from nsj_jobs.dao import Tpedido
from datetime import datetime
from nsj_jobs.resources.dom.minidom import Document

#from xml.etree.ElementTree import Element,  SubElement,  Comment,  tostring
# import urllib


def montar_LayoutCalculaImpostos(t_Pedido: Tpedido, pathFile, num_notaFiscal):

    arquivo_nome = formataNumZeros(
        30, int(t_Pedido.pedido['num_pedido']))
    arquivo_xml = pathFile + '\\' + arquivo_nome

    if t_Pedido.pedido['tipo_nota'] == 'NFE':
        arquivo_xml = arquivo_xml + '.xml'
        return montar_xml_nfe(t_Pedido, arquivo_xml)
    elif t_Pedido.pedido['tipo_nota'] == 'NFSE':
        arquivo_xml = arquivo_xml + '_nfse.xml'
        return montar_xml_nfse(t_Pedido, arquivo_xml)
    else: 
        raise Exception('Tipo de nota inválido.')


def montar_xml_nfse(t_Pedido: Tpedido, arquivo_xml):
    # Criando um arquivo para escrita
    output = open(arquivo_xml, "w")

    # Criando um minidom-document
    doc = Document()

    # Criando a base geral do elemento
    NSJDOC = doc.createElement('NSJDOC')
    NSJDOC.setAttribute('xmlns', 'http://www.nasajon.com.br/docengine')
    doc.appendChild(NSJDOC)
    base = createNode('NFSE', NSJDOC, doc)

    # NFE
    createNodeChild(
        'GRUPOEMPRESARIAL', t_Pedido.lstEstabelecimento[0]['grupoempresarial'], doc, base)
    createNodeChild(
        'ESTABELECIMENTO', t_Pedido.lstEstabelecimento[0]['estabelecimento'], doc, base)
    
    # DADOSGERAIS
    nivel_1 = createNode('DADOSGERAIS', base, doc)
    createNodeChild(
        'SERIE', t_Pedido.pedido['serie_nf'],  doc, nivel_1)
    createNodeChild(
        'SUBSERIE', t_Pedido.pedido['subserie'], doc, nivel_1)
    createNodeChild(
        'DATAEMISSAO', t_Pedido.pedido['datasaidaentrada'], doc, nivel_1)
    createNodeChild('DATASAIDAENTRADA',
                    t_Pedido.pedido['datasaidaentrada'], doc, nivel_1)
    createNodeChild('DATALANCAMENTO',
                    t_Pedido.pedido['datalancamento'], doc, nivel_1)
    createNodeChild(
        'MUNICIPIOGERADOR', t_Pedido.pedido['municipio_gerador'], doc, nivel_1)
    createNodeChild('CADASTRADOPOR', 'MESTRE', doc, nivel_1)
    # DESTINATARIO
    nivel_1 = createNode('DESTINATARIO', base, doc)
    createNodeChild(
        'CODIGO', t_Pedido.lstCliente[0]['codigo'], doc, nivel_1)
    createNodeChild(
        'CPF_CNPJ', t_Pedido.lstCliente[0]['cpf_cnpj'], doc, nivel_1)
    createNodeChild('NOME', t_Pedido.lstCliente[0]['nome'], doc, nivel_1)
    createNodeChild(
        'NOMEFANTASIA', t_Pedido.lstCliente[0]['nomefantasia'], doc, nivel_1)
    createNodeChild('EMAIL', t_Pedido.lstCliente[0]['email'], doc, nivel_1)

    # ENDERECO
    nivel_2 = createNode('ENDERECO', nivel_1, doc)
    createNodeChild(
        'TIPOLOGRADOURO', t_Pedido.endPrestacao['tipo_logradouro'], doc, nivel_2)
    createNodeChild(
        'LOGRADOURO', t_Pedido.endPrestacao['logradouro'], doc, nivel_2)
    createNodeChild(
        'NUMERO', t_Pedido.endPrestacao['numero'], doc, nivel_2)
    createNodeChild(
        'COMPLEMENTO', t_Pedido.endPrestacao['complemento'], doc, nivel_2)
    createNodeChild(
        'BAIRRO', t_Pedido.endPrestacao['bairro'], doc, nivel_2)
    createNodeChild(
        'CODIGOMUNICIPIO', t_Pedido.endPrestacao['codigo_municipio'], doc, nivel_2)
    createNodeChild(
        'MUNICIPIO', t_Pedido.endPrestacao['nome_municipio'], doc, nivel_2)
    createNodeChild('UF', t_Pedido.endPrestacao['uf'], doc, nivel_2)
    createNodeChild('CEP', t_Pedido.endPrestacao['cep'], doc, nivel_2)
    createNodeChild(
        'PAIS', t_Pedido.endPrestacao['codigo_pais'], doc, nivel_2)
    createNodeChild(
        'PAISNOME', t_Pedido.endPrestacao['nome_pais'], doc, nivel_2)
    createNodeChild(
        'TELEFONE', t_Pedido.endPrestacao['telefone'], doc, nivel_2)
    createNodeChild(
        'REFERENCIA', t_Pedido.endPrestacao['referencia'], doc, nivel_2)

    # SERVIÇOS
    nivel_1 = createNode('SERVICOS', base, doc)
    for servico in t_Pedido.lstServicos:
        nivel_2 = createNode('SERVICO', nivel_1, doc)
        createNodeChild('CODIGO', servico.get('codigo'), doc, nivel_2)
        createNodeChild('QUANTIDADE', servico.get('quantidade'), doc, nivel_2)
        createNodeChild('VALORUNITARIO', servico.get(
            'valor_unitario'), doc, nivel_2)
        createNodeChild('VALORDESCONTO', servico.get(
            'valordesconto'), doc, nivel_2)

    # FORMA DE PAGAMENTO
    nivel_1 = createNode('FORMASPAGAMENTOS', base, doc)
    for pagamento in t_Pedido.lstFormaPagamento:
        nivel_2 = createNode('FORMAPAGAMENTO', nivel_1, doc)
        createNodeChild('TIPOFORMAPAGAMENTO', pagamento.get(
            'tipoformapagamento'), doc, nivel_2)
        nivel_3 = createNode('PARCELAS', nivel_2, doc)
        for parcela in pagamento.get('parcelas'):
            nivel_4 = createNode('PARCELA', nivel_3, doc)
            createNodeChild('NUMERO', parcela.get('numero'), doc, nivel_4)
            createNodeChild('VENCIMENTO', parcela.get(
                'vencimento'), doc, nivel_4)
            createNodeChild('VALOR', parcela.get('valor'), doc, nivel_4)
        createNodeChild('VALOR', pagamento.get('valor_total'), doc, nivel_2)

    doc.writexml(output, " ", " ", "\n", "UTF-16")
    # Fechando o arquivo
    output.close()
    return arquivo_xml


def montar_xml_nfe(t_Pedido: Tpedido, arquivo_xml):
    # Criando um arquivo para escrita
    output = open(arquivo_xml, "w")

    # Criando um minidom-document
    doc = Document()

    # Criando a base geral do elemento
    NSJDOC = doc.createElement('NSJDOC')
    NSJDOC.setAttribute('xmlns', 'http://www.nasajon.com.br/docengine')
    doc.appendChild(NSJDOC)
    base = createNode('NFE', NSJDOC, doc)

    # NFE
    createNodeChild(
        'GRUPOEMPRESARIAL', t_Pedido.lstEstabelecimento[0]['grupoempresarial'], doc, base)
    createNodeChild(
        'EMPRESA', t_Pedido.lstEstabelecimento[0]['empresa'], doc, base)
    createNodeChild(
        'ESTABELECIMENTO', t_Pedido.lstEstabelecimento[0]['estabelecimento'], doc, base)
    createNodeChild('VERSAO', '4.00', doc, base)
    createNodeChild('SOMENTE_IMPORTACAO', 1 if not t_Pedido.pedido["emitir_nota"] else 0, doc, base)
    createNodeChild('OBSERVACAO',
                    t_Pedido.pedido['observacao'], doc, base)

    # DADOSGERAIS
    nivel_1 = createNode('DADOSGERAIS', base, doc)
    createNodeChild(
        'SERIE', t_Pedido.pedido['serie_nf'],  doc, nivel_1)
    createNodeChild(
        'SUBSERIE', t_Pedido.pedido['subserie'], doc, nivel_1)
    createNodeChild(
        'DATAEMISSAO', t_Pedido.pedido['datasaidaentrada'], doc, nivel_1)
    createNodeChild('DATASAIDAENTRADA',
                    t_Pedido.pedido['datasaidaentrada'], doc, nivel_1)
    createNodeChild('DATALANCAMENTO',
                    t_Pedido.pedido['datalancamento'], doc, nivel_1)
    createNodeChild(
        'OPERACAO', t_Pedido.pedido['operacao'], doc, nivel_1)
    createNodeChild(
        'MODELO', t_Pedido.pedido['tipodocumento'], doc, nivel_1)
    createNodeChild(
        'TIPOOPERACAO', t_Pedido.pedido['tp_operacao'], doc, nivel_1)
    createNodeChild(
        'LOCALESTOQUE', t_Pedido.pedido['localestoque'], doc, nivel_1)
    createNodeChild('FORMAPAGAMENTO',
                    t_Pedido.pedido['formapagamento'], doc, nivel_1)
    createNodeChild('REFERENCIAEXTERNA',
                    t_Pedido.pedido['num_externo'], doc, nivel_1)
    createNodeChild('CADASTRADOPOR', 'MESTRE', doc, nivel_1)
    
    if t_Pedido.pedido['consumidorfinal'] != '':
        createNodeChild('INDICADORFINALIDADE', t_Pedido.pedido['consumidorfinal'], doc, nivel_1)
          

    # DESTINATARIO
    nivel_1 = createNode('DESTINATARIO', base, doc)
    createNodeChild(
        'CODIGO', t_Pedido.lstCliente[0]['codigo'], doc, nivel_1)
    createNodeChild(
        'CPF_CNPJ', t_Pedido.lstCliente[0]['cpf_cnpj'], doc, nivel_1)
    createNodeChild('NOME', t_Pedido.lstCliente[0]['nome'], doc, nivel_1)
    createNodeChild(
        'NOMEFANTASIA', t_Pedido.lstCliente[0]['nomefantasia'], doc, nivel_1)
    createNodeChild('CONTRIBUINTEICMS', str(
        t_Pedido.lstCliente[0]['contribuinteicms']), doc, nivel_1)
    createNodeChild(
        'INSCRICAOESTADUAL', t_Pedido.lstCliente[0]['inscricaoestadual'], doc, nivel_1)
    createNodeChild('EMAIL', t_Pedido.lstCliente[0]['email'], doc, nivel_1)

    # ENDERECO
    nivel_2 = createNode('ENDERECO', nivel_1, doc)
    createNodeChild(
        'TIPOLOGRADOURO', t_Pedido.lstEndCliente[0]['tipologradouro'], doc, nivel_2)
    createNodeChild(
        'LOGRADOURO', t_Pedido.lstEndCliente[0]['logradouro'], doc, nivel_2)
    createNodeChild(
        'NUMERO', t_Pedido.lstEndCliente[0]['numero'], doc, nivel_2)
    createNodeChild(
        'COMPLEMENTO', t_Pedido.lstEndCliente[0]['complemento'], doc, nivel_2)
    createNodeChild(
        'BAIRRO', t_Pedido.lstEndCliente[0]['bairro'], doc, nivel_2)
    createNodeChild(
        'CODIGOMUNICIPIO', t_Pedido.lstEndCliente[0]['codigomunicipio'], doc, nivel_2)
    createNodeChild(
        'MUNICIPIO', t_Pedido.lstEndCliente[0]['municipio'], doc, nivel_2)
    createNodeChild('UF', t_Pedido.lstEndCliente[0]['uf'], doc, nivel_2)
    createNodeChild('CEP', t_Pedido.lstEndCliente[0]['cep'], doc, nivel_2)
    createNodeChild(
        'PAIS', t_Pedido.lstEndCliente[0]['pais'], doc, nivel_2)
    createNodeChild(
        'PAISNOME', t_Pedido.lstEndCliente[0]['paisnome'], doc, nivel_2)
    createNodeChild(
        'TELEFONE', t_Pedido.lstEndCliente[0]['telefone'], doc, nivel_2)
    createNodeChild(
        'REFERENCIA', t_Pedido.lstEndCliente[0]['referencia'], doc, nivel_2)

    # ENDERECO DE ENTREGA
    if t_Pedido.endEntrega:
        nivel_1 = createNode('ENTREGA', base, doc)
        createNodeChild(
            'TIPOLOGRADOURO', t_Pedido.endEntrega['tipo_logradouro'], doc, nivel_1)
        createNodeChild(
            'LOGRADOURO', t_Pedido.endEntrega['logradouro'], doc, nivel_1)
        createNodeChild(
            'NUMERO', t_Pedido.endEntrega['numero'], doc, nivel_1)
        createNodeChild(
            'COMPLEMENTO', t_Pedido.endEntrega['complemento'], doc, nivel_1)
        createNodeChild('CEP', t_Pedido.endEntrega['cep'], doc, nivel_1)
        createNodeChild(
            'BAIRRO', t_Pedido.endEntrega['bairro'], doc, nivel_1)
        createNodeChild(
            'CODIGOMUNICIPIO', t_Pedido.endEntrega['codigo_municipio'], doc, nivel_1)
        createNodeChild(
            'MUNICIPIO', t_Pedido.endEntrega['nome_municipio'], doc, nivel_1)
        createNodeChild('UF', t_Pedido.endEntrega['uf'], doc, nivel_1)
        createNodeChild(
            'PAIS', t_Pedido.endEntrega['codigo_pais'], doc, nivel_1)

    # PRODUTOS
    valor_total_nota = 0
    for produto in t_Pedido.lstProdutos:
        valor_total_nota = valor_total_nota + \
            float(produto.get('valortotalbruto'))

        nivel_1 = createNode('LINHA', base, doc)
        nivel_2 = createNode('PROD', nivel_1, doc)

        createNodeChild('PRODUTO', produto.get(
            'cod_produto'), doc, nivel_2)
        createNodeChild('DESCRICAOPRODUTO', produto.get(
            'especificacao'), doc, nivel_2)
        createNodeChild('CODIGOBARRAS', 'SEM GTIN', doc, nivel_2)
        createNodeChild('NCM', produto.get('tipi'), doc, nivel_2)
        createNodeChild('UNIDADE', produto.get(
            'cod_unidade'), doc, nivel_2)
        createNodeChild('QUANTIDADE', produto.get(
            'quantidade'), doc, nivel_2)
        createNodeChild('VALORUNITARIO', produto.get(
            'valor_unitario'), doc, nivel_2)
        createNodeChild('VALORTOTALBRUTO', produto.get(
            'valortotalbruto'), doc, nivel_2)
        createNodeChild('VALORDESCONTO', produto.get(
            'valordesconto'), doc, nivel_2)
        createNodeChild('LOCALESTOQUE', produto.get(
            'localestoque'), doc, nivel_2)
        createNodeChild('FIGURATRIBUTARIA', produto.get(
            'figuratributaria'), doc, nivel_2)
        createNodeChild('CFOP', produto.get('cfop'), doc, nivel_2)
        createNodeChild('VALORFRETE', produto.get(
            'valorfrete'), doc, nivel_2)
        createNodeChild('VALORSEGURO', produto.get(
            'valorseguro'), doc, nivel_2)
        createNodeChild('VALOROUTRASDESPESAS', produto.get(
            'valoroutrasdespesas'), doc, nivel_2)

    nivel_1 = createNode('INFORMACOESADICIONAIS', base, doc)
    createNodeChild('INFORMACOESMANUAIS',
                    t_Pedido.pedido['observacao'], doc, nivel_1)

    # FORMA DE PAGAMENTO
    nivel_1 = createNode('COBRANCA', base, doc)
    parc_num = 1
    for pagamento in t_Pedido.lstFormaPagamento:
        strNumParc = formataNumZeros(3, parc_num)
        nivel_2 = createNode('DUPLICATA', nivel_1, doc)
        createNodeChild('TIPOFORMAPAGAMENTO', pagamento.get(
            'tipoformapagamento'), doc, nivel_2)
        createNodeChild('NUMERO', strNumParc, doc, nivel_2)
        createNodeChild('VENCIMENTO', pagamento.get(
            'dt_vencimento'), doc, nivel_2)
        createNodeChild('VALOR', pagamento.get(
            'valor_parcela'), doc, nivel_2)
        parc_num += 1

    doc.writexml(output, " ", " ", "\n", "UTF-16")
    # Fechando o arquivo
    output.close()
    return arquivo_xml


def createNode(titulo, nodepai, documento):
    node = documento.createElement(titulo)
    return nodepai.appendChild(node)


def createNodeChild(titulo, valor, documento, nodepai):
    value_node = str(valor)
    if (value_node == 'None'):
        value_node = ''

    node = documento.createElement(titulo)
    conteudo = documento.createTextNode(value_node)
    node.appendChild(conteudo)
    nodepai.appendChild(node)


def closeNode(nodepai, node):
    nodepai.appendChild(node)


def formataNumZeros(quant_zeros: int, numero: int) -> str:
    sfmt = '%0{}d'.format(quant_zeros)
    num_zeros = sfmt % (numero,)
    return num_zeros
