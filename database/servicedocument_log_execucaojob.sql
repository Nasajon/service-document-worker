
CREATE TABLE servicedocument.log_execucaojob
(
  id_log uuid NOT NULL DEFAULT uuid_generate_v4(),
  id_pedido uuid NOT NULL,
  datahora timestamp without time zone NOT NULL DEFAULT now(),
  tipo smallint NOT NULL, -- 0 - Mensagem de Sucesso; 1 - Mensagem de Erro; 2 - Dados inconsistentes no registro; 3 - Mensagem de retorno do Service Document
  mensagem text,
  id_doc_service_msg uuid,
  lastupdate timestamp without time zone,
  tenant bigint,
  ultimaexecucao timestamp(0) without time zone,
  CONSTRAINT pk_log_execucaojob PRIMARY KEY (id_log),
  CONSTRAINT "fk_log_execucaojob.pedido" FOREIGN KEY (id_pedido)
      REFERENCES servicedocument.pedidos (id_pedido) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT "log_execucaojob.documento" FOREIGN KEY (id_doc_service_msg)
      REFERENCES servicedocument.documentos (documento) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);
