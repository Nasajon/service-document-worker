CREATE TABLE servicedocument.pagamentos
(
  id_formapagamento uuid NOT NULL DEFAULT uuid_generate_v4(),
  id_pedido uuid NOT NULL,
  cod_tipopagamento character varying(30) NOT NULL,
  valor_parcela numeric(20,2) NOT NULL,
  dt_vencimento date NOT NULL,
  lastupdate timestamp without time zone,
  tenant bigint,
  numero int,
  CONSTRAINT formapagamento_id_formapagamento_pk PRIMARY KEY (id_formapagamento),
  CONSTRAINT formapagamento_id_pedido_fk FOREIGN KEY (id_pedido)
      REFERENCES servicedocument.pedidos (id_pedido) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);