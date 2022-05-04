from app.settings import flask_app
from app.service.build_service import BuildService
from flask import request
from nsj_gcf_utils.exception import NotFoundException
from nsj_gcf_utils.json_util import json_dumps
from nsj_gcf_utils.rest_error_util import format_json_error

BUILD_ROUTE = f'/build/<branch>'

@flask_app.route(BUILD_ROUTE, methods=['GET'])
def build(branch: str):
    try:
        build_service = BuildService()
        image_name = build_service.execute(branch)
        response = {
            "image_name": image_name
        }
        return (json_dumps(response), 200, {})
    except Exception as e:
        error = {
            "error": str(e)
        }
        return (json_dumps(error), 400, {})

