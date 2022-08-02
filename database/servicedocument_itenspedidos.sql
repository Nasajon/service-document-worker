
CREATE TABLE servicedocument.itenspedidos
(
  id_item_pedido uuid NOT NULL DEFAULT uuid_generate_v4(),
  id_pedido uuid NOT NULL,
  cod_produto character varying(60) NOT NULL,
  valor_unitario numeric(20,2) NOT NULL,
  valor_desconto numeric(20,2) DEFAULT 0,
  quantidade numeric(20,4) NOT NULL,
  localestoque character varying(30) NOT NULL,
  cfop character varying(30) NOT NULL,
  lastupdate timestamp without time zone,
  tenant bigint,
  documentoreferenciado_chave character varying(44),
  CONSTRAINT itempedido_id_item_pedido_pk PRIMARY KEY (id_item_pedido),
  CONSTRAINT itempedido_id_pedido_fk FOREIGN KEY (id_pedido)
      REFERENCES servicedocument.pedidos (id_pedido) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);