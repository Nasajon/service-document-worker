from app.settings import flask_app
from app.service.build_service import BuildService
from nsj_gcf_utils.json_util import json_dumps

BUILD_ROUTE = f'/build/<branch>'

@flask_app.route(BUILD_ROUTE, methods=['GET'])
def build(branch: str):
    try:
        build_service = BuildService()
        response = build_service.execute(branch)
        return (json_dumps(response), 200, {})
    except Exception as e:
        error = {
            "error": str(e)
        }
        return (json_dumps(error), 400, {})

