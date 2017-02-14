from transform import app
from transform import settings
import logging
from structlog import wrap_logger
from flask import request, make_response, send_file, jsonify
from transform.transformers import PDFTransformer, ImageTransformer, CORATransformer
from jinja2 import Environment, PackageLoader

import json
import os.path

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

        with open("./transform/surveys/%s.%s.json" % (survey_response['survey_id'], form_id)) as json_file:
            return json.load(json_file)
    except IOError:
        return False


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


@app.route('/pdf', methods=['POST'])
def render_pdf():
    survey_response = request.get_json(force=True)

    survey = get_survey(survey_response)

    if not survey:
        return client_error("PDF:Unsupported survey/instrument id")

    try:
        pdf = PDFTransformer(survey, survey_response)
        rendered_pdf = pdf.render()

    except IOError as e:
        return client_error("PDF:Could not render pdf buffer: %s" % repr(e))

    response = make_response(rendered_pdf)
    response.mimetype = 'application/pdf'

    logger.info("PDF:SUCCESS")

    return response


@app.route('/images', methods=['POST'])
def render_images():
    survey_response = request.get_json(force=True)

    survey = get_survey(survey_response)

    if not survey:
        return client_error("IMAGES:Unsupported survey/instrument id")

    itransformer = ImageTransformer(logger, survey, survey_response)

    try:
        path = itransformer.create_pdf(survey, survey_response)
        images = list(itransformer.create_image_sequence(path))
        index = itransformer.create_image_index(images)
        zipfile = itransformer.create_zip(images, index)
        locn = os.path.dirname(path)
        itransformer.cleanup(locn)
    except IOError as e:
        logger.error(e)
        return client_error("IMAGES:Could not create zip buffer: %s" % repr(e))

    logger.info("IMAGES:SUCCESS")

    return send_file(zipfile, mimetype='application/zip', add_etags=False)


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

    ctransformer = CORATransformer(logger, survey, survey_response, batch_number, sequence_no)

    try:
        pdf = ctransformer.create_formats()
        ctransformer.prepare_archive()
        zipfile = ctransformer.create_zip()
        locn = os.path.dirname(pdf)
        ctransformer.cleanup(locn)
    except IOError as e:
        return client_error("CORA:Could not create zip buffer: %s" % repr(e))
    except Exception as e:
        return server_error(e)

    return send_file(zipfile, mimetype='application/zip', add_etags=False)


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({'status': 'OK'})
