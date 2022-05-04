# Importando arquivos de configuração
from app.settings import flask_app

# TODO Importar todos os controllers (se não, as rotas não existirão)
import app.controller.build_controller

if __name__ == '__main__':
    flask_app.run(port=5000)
