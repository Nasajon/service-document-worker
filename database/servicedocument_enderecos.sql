
CREATE TABLE servicedocument.enderecos
(
  endereco uuid NOT NULL DEFAULT uuid_generate_v4(),
  id_pedido uuid NOT NUll,
  tipo_logradouro varchar(10),
  logradouro varchar(150),
  numero varchar(10),
  complemento varchar(60),
  cep varchar(8),
  bairro varchar(60),
  codigo_municipio varchar(8),
  nome_municipio varchar(60),
  codigo_pais varchar(5),
  uf varchar(2),
  lastupdate timestamp without time zone DEFAULT now(),
  nome_pais varchar(60),
  referencia varchar(60),
  telefone varchar(15),
  tipo_endereco integer NOT NULL DEFAULT 0,
  CONSTRAINT "PK_enderecos_endereco" PRIMARY KEY (endereco),
  CONSTRAINT "FK_servicedocument.enderecos.id_pedido" FOREIGN KEY (id_pedido)
      REFERENCES servicedocument.pedidos (id_pedido) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);

COMMENT ON COLUMN servicedocument.enderecos.tipo_endereco is '0 - Entrega, 1 - Prestação de Serviço';