﻿CREATE TABLE servicedocument.pedidos
(
  id_pedido uuid NOT NULL DEFAULT uuid_generate_v4(),
  num_pedido serial NOT NULL,
  cnpj_estabelecimento character varying(14) NOT NULL,
  cnpj_cliente character varying(14) NOT NULL,
  cod_operacao character varying(30) NOT NULL,
  tp_operacao integer NOT NULL,
  dt_emissao date NOT NULL,
  num_externo character varying(10),
  valor_pedido numeric(20,2) NOT NULL,
  status integer DEFAULT 0,
  tipodocumento integer NOT NULL,
  localestoque character varying(30) NOT NULL,
  cfop character varying(30) NOT NULL,
  mensagem character varying(100),
  chave_de_acesso character varying(44),
  numero_nf character varying(15),
  serie_nf character varying(3),
  id_docfis uuid,
  processado boolean NOT NULL DEFAULT false,
  datahora_processamento timestamp(0) without time zone,
  emitir boolean NOT NULL DEFAULT false,
  observacao character varying(5048),
  lastupdate timestamp without time zone,
  tenant bigint,
  tentativas_adicionais int4 NULL DEFAULT 0,
  primeira_tentativa timestamp NULL,
  ultima_tentativa timestamp NULL,
  CONSTRAINT pedido_id_pedido_pk PRIMARY KEY (id_pedido)
);