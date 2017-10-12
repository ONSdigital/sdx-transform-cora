import json
import logging
import os.path

from flask import send_file
from jinja2 import Environment
from jinja2 import PackageLoader
from sdx.common.transformer import ImageTransformer
from sdx.common.transformer import PDFTransformer
from structlog import wrap_logger

from transform import app
from transform import settings

logger = wrap_logger(logging.getLogger(__name__))

env = Environment(loader=PackageLoader('transform', 'templates'))

test_message = """{
   "type": "uk.gov.ons.edc.eq:surveyresponse",
   "origin": "uk.gov.ons.edc.eq",
   "survey_id": "144",
   "version": "0.0.1",
   "collection": {
     "exercise_sid": "hfjdskf",
     "instrument_id": "0001",
     "period": "201605"
   },
   "submitted_at": "2016-03-12T10:39:40Z",
   "metadata": {
     "user_id": "789473423",
     "ru_ref": "12345678901A"
   },
   "data": {
        "0210": "1",
        "0220": "0",
        "0230": "1",
        "0240": "0",
        "0410": "1",
        "0420": "0",
        "0430": "1",
        "0440": "0",
        "2310": "1",
        "2320": "0",
        "2330": "1",
        "2340": "0",
        "1310": "0",
        "2675": "0",
        "2676": "1",
        "2677": "0",
        "1410": "123456",
        "1320": "1",
        "1420": "123456",
        "1331": "0",
        "1332": "1",
        "1333": "0",
        "1430": "123456",
        "1340": "1",
        "1440": "123456",
        "1350": "0",
        "1450": "123456",
        "1360": "1",
        "1460": "123456",
        "1371": "0",
        "1372": "1",
        "1373": "0",
        "1374": "1",
        "1470": "123456",
        "0510": "yes",
        "0610": "0",
        "0620": "1",
        "0630": "0",
        "0520": "yes",
        "0601": "0",
        "0602": "1",
        "0603": "0",
        "0710": "0",
        "0720": "1",
        "0810": "123",
        "0820": "010",
        "0830": "789",
        "0840": "963",
        "0900": "yes",
        "1010": "0",
        "1020": "1",
        "1030": "0",
        "1100": "yes",
        "1510": "1",
        "1530": "0",
        "1520": "1",
        "2657": "0100",
        "2658": "1000",
        "2659": "0001",
        "2660": "0010",
        "2661": "0100",
        "2662": "1000",
        "2663": "0001",
        "2664": "0010",
        "2665": "0100",
        "2666": "1000",
        "2667": "0001",
        "2011": "1",
        "2020": "0",
        "2030": "1",
        "2040": "0",
        "1210": "0100",
        "1211": "1000",
        "1220": "0001",
        "1230": "0010",
        "1240": "0100",
        "1250": "1000",
        "1290": "0001",
        "1260": "0010",
        "1270": "0100",
        "1212": "1000",
        "1213": "0001",
        "1280": "0010",
        "1601": "0001",
        "1620": "0010",
        "1631": "0100",
        "1632": "1000",
        "1640": "0001",
        "1650": "0010",
        "1660": "0100",
        "1670": "1000",
        "1680": "0001",
        "1610": "0010",
        "1611": "0100",
        "1690": "1000",
        "1811": "0",
        "1812": "1",
        "1813": "0",
        "1814": "1",
        "1821": "1",
        "1822": "0",
        "1823": "1",
        "1824": "0",
        "1881": "0",
        "1882": "1",
        "1883": "0",
        "1884": "1",
        "1891": "1",
        "1892": "0",
        "1893": "1",
        "1894": "0",
        "1841": "0",
        "1842": "1",
        "1843": "0",
        "1844": "1",
        "1851": "1",
        "1852": "0",
        "1853": "1",
        "1854": "0",
        "1861": "0",
        "1862": "1",
        "1863": "0",
        "1864": "1",
        "1871": "1",
        "1872": "0",
        "1873": "1",
        "1874": "0",
        "2650": "0001",
        "2651": "0010",
        "2652": "0100",
        "2653": "1000",
        "2654": "0001",
        "2655": "0010",
        "2656": "0100",
        "2668": "0",
        "2669": "1",
        "2670": "0",
        "2671": "1",
        "2672": "0",
        "2673": "1",
        "2674": "0",
        "2410": "123456",
        "2420": "123456",
        "2440": "123456",
        "2510": "4567890",
        "2520": "1234567",
        "2610": "963",
        "2620": "123",
        "2631": "1",
        "2632": "0",
        "2633": "1",
        "2634": "0",
        "2635": "1",
        "2636": "0",
        "2678": "0",
        "2700": "1",
        "2800": "000",
        "2801": "10",
        "2900": "no"
    }
}"""


@app.route('/images-test', methods=['GET'])
def images_test():
    survey_response = json.loads(test_message)
    form_id = survey_response['collection']['instrument_id']

    with open("./transform/surveys/%s.%s.json" % (survey_response['survey_id'], form_id)) as json_file:
        survey = json.load(json_file)

        itransformer = ImageTransformer(logger, settings, survey, survey_response)

        path = PDFTransformer.render_to_file(survey, survey_response)
        locn = os.path.dirname(path)
        images = list(itransformer.create_image_sequence(path))
        index = itransformer.create_image_index(images)
        zipfile = itransformer.create_zip(images, index)

        itransformer.cleanup(locn)

        return send_file(zipfile, mimetype='application/zip')


@app.route('/html-test', methods=['GET'])
def html_test():

    response = json.loads(test_message)
    template = env.get_template('html.tmpl')
    form_id = response['collection']['instrument_id']

    with open("./transform/surveys/%s.%s.json" % (response['survey_id'], form_id)) as json_file:
        survey = json.load(json_file)
        return template.render(response=response, survey=survey)
