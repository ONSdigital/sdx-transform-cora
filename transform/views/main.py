import json
import logging
import os.path

from flask import request, send_file, jsonify
from jinja2 import Environment, PackageLoader
import pkg_resources
from structlog import wrap_logger

from transform import app
from transform import settings
from transform.transformers import CORATransformer

env = Environment(loader=PackageLoader('transform', 'templates'))

logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
logger = wrap_logger(logging.getLogger(__name__))


@app.errorhandler(400)
def errorhandler_400(e):
    return client_error(repr(e))


def client_error(error=None):
    logger.error("Client error", error=error)
    message = {
        'status': 400,
        'message': error,
        'uri': request.url,
    }
    resp = jsonify(message)
    resp.status_code = 400

    return resp


@app.errorhandler(500)
def server_error(error=None):
    logger.error("Server error", error=repr(error))
    message = {
        'status': 500,
        'message': "Internal server error: " + repr(error),
    }
    resp = jsonify(message)
    resp.status_code = 500

    return resp


def get_survey(survey_response):
    try:
        form_id = survey_response['collection']['instrument_id']
        filename = ("../surveys/%s.%s.json" % (survey_response['survey_id'], form_id))
        content = pkg_resources.resource_string(__name__, filename)

    except FileNotFoundError:
        return None
    else:
        return json.loads(content.decode("utf-8"))


@app.route('/idbr', methods=['POST'])
def render_idbr():
    response = request.get_json(force=True)
    template = env.get_template('idbr.tmpl')

    logger.info("IDBR:SUCCESS")

    return template.render(response=response)


@app.route('/html', methods=['POST'])
def render_html():
    response = request.get_json(force=True)
    template = env.get_template('html.tmpl')

    survey = get_survey(response)

    if not survey:
        return client_error("HTML:Unsupported survey/instrument id")

    logger.info("HTML:SUCCESS")

    return template.render(response=response, survey=survey)


@app.route('/cora', methods=['POST'])
@app.route('/cora/<sequence_no>', methods=['POST'])
@app.route('/cora/<sequence_no>/<batch_number>', methods=['POST'])
def cora_view(sequence_no=1000, batch_number=False):
    survey_response = request.get_json(force=True)

    if batch_number:
        batch_number = int(batch_number)

    if sequence_no:
        sequence_no = int(sequence_no)

    survey = get_survey(survey_response)

    if not survey:
        return client_error("CORA:Unsupported survey/instrument id")

    ctransformer = CORATransformer(logger, settings, survey, survey_response, batch_number, sequence_no)

    try:
        pdf = ctransformer.create_formats()
        locn = os.path.dirname(pdf)
        ctransformer.prepare_archive()
        zipfile = ctransformer.create_zip()
    except IOError as e:
        return client_error("CORA:Could not create zip buffer: %s" % repr(e))
    except Exception as e:
        return server_error(e)

    try:
        ctransformer.cleanup(locn)
    except Exception as e:
        return client_error("CORA:Could not delete tmp files: %s" % repr(e))

    return send_file(zipfile, mimetype='application/zip', add_etags=False)


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({'status': 'OK'})
