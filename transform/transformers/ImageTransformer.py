#!/usr/bin/env python
#   coding: UTF-8

import argparse
import datetime
import dateutil.parser
import glob
from io import BytesIO
import itertools
import json
import logging
import os.path
import shutil
import subprocess
import sys
import zipfile

from requests.packages.urllib3.exceptions import MaxRetryError

try:
    from PDFTransformer import PDFTransformer
except ImportError:
    from .PDFTransformer import PDFTransformer

try:
    from transform import settings
    from transform.settings import session
    from transform.views.image_filters import get_env, format_date
except ImportError:
    print("Available for command line operation only", file=sys.stderr)

__doc__ = """
SDX Image Transformer.

Example:

python transform/transformers/ImageTransformer.py --survey transform/surveys/144.0001.json \\
< tests/replies/ukis-01.json > output.zip

"""


class ImageTransformer(object):

    @staticmethod
    def create_pdf(survey, data):
        '''
        Create a pdf which will be used as the basis for images
        '''
        pdf_transformer = PDFTransformer(survey, data)
        return pdf_transformer.render_to_file()

    @staticmethod
    def extract_pdf_images(path, fileName):
        '''
        Extract all pdf pages as jpegs
        '''
        rootName, _ = os.path.splitext(fileName)
        subprocess.call(
            ["pdftoppm", "-jpeg", fileName, rootName],
            cwd=path
        )
        return glob.glob("%s/%s-*.jpg" % (path, rootName))

    def __init__(self, logger, survey, response_data, sequence_no=1000):
        self.logger = logger
        self.survey = survey
        self.response = response_data
        self.sequence_no = sequence_no

    def get_image_sequence_numbers(self):
        sequence_numbers = []
        for image in self.images:
            sequence_number = self.get_image_sequence_no()
            sequence_numbers.append(sequence_number)

        self.logger.debug('Sequence numbers generated', sequence_numbers=sequence_numbers)
        return sequence_numbers

    def create_image_sequence(self, path, numberSeq=None):
        '''
        Renumber the image sequence extracted from pdf
        '''
        locn, baseName = os.path.split(path)
        self.images = ImageTransformer.extract_pdf_images(locn, baseName)
        numberSeq = numberSeq or self.get_image_sequence_numbers()
        for imageFile, n in zip(self.images, numberSeq):
            name = "S%09d.JPG" % n
            fP = os.path.join(locn, name)
            os.rename(imageFile, fP)
            yield fP

    def create_image_index(self, images):
        '''
        Takes a list of images and creates a index csv from them
        '''
        if not images:
            return None
        env = get_env()
        template = env.get_template('csv.tmpl')

        current_time = datetime.datetime.utcnow()
        creation_time = {
            'short': format_date(current_time, 'short'),
            'long': format_date(current_time)
        }
        submission_date = dateutil.parser.parse(self.response['submitted_at'])
        submission_date_str = format_date(submission_date, 'short')

        image_path = settings.FTP_HOST + settings.SDX_FTP_IMAGES_PATH + "\\Images"
        template_output = template.render(
            SDX_FTP_IMAGES_PATH=image_path,
            images=[os.path.basename(i) for i in images],
            response=self.response, creation_time=creation_time
        )

        # Log all file paths
        msg = "ADDING IMAGE TO INDEX"
        [self.logger.info(msg, file=(image_path + os.path.basename(i))) for i in images]

        self.index_file = "EDC_%s_%s_%04d.csv" % (self.survey['survey_id'], submission_date_str, self.sequence_no)

        locn = os.path.dirname(images[0])
        path = os.path.join(locn, self.index_file)
        with open(path, "w") as fh:
            fh.write(template_output)
        return path

    def create_zip(self, images, index):
        '''
        Create a zip from a renumbered sequence
        '''
        in_memory_zip = BytesIO()

        with zipfile.ZipFile(in_memory_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for fP in images:
                fN = os.path.basename(fP)
                try:
                    zipf.write(fP, arcname=fN)
                except Exception as e:
                    self.logger.error(e)

            if index:
                fN = os.path.basename(index)
                zipf.write(index, arcname=fN)

        # Return to beginning of file
        in_memory_zip.seek(0)

        return in_memory_zip

    def cleanup(self, locn):
        '''
        Remove all temporary files, by removing top level dir
        '''
        shutil.rmtree(locn)

    def response_ok(self, res):
        if res.status_code == 200:
            self.logger.info("Returned sdx-sequence", request_url=res.url, status=res.status_code)
            return True
        else:
            self.logger.error("Returned from sdx-sequence", request_url=res.url, status=res.status_code)
            return False

    def remote_call(self, request_url, json=None):
        try:
            self.logger.info("Calling sdx-sequence", request_url=request_url)

            r = None

            if json:
                r = session.post(request_url, json=json)
            else:
                r = session.get(request_url)

            return r
        except MaxRetryError:
            self.logger.error("Max retries exceeded (5)", request_url=request_url)

    def get_image_sequence_no(self):
        sequence_url = settings.SDX_SEQUENCE_URL + "/image-sequence"

        r = self.remote_call(sequence_url)

        if not self.response_ok(r):
            return False

        result = r.json()
        return result['sequence_no']


def parser(description=__doc__):
    rv = argparse.ArgumentParser(
        description,
    )
    rv.add_argument(
        "--survey", required=True,
        help="Set a path to the survey JSON file.")
    return rv


def main(args):
    log = logging.getLogger("ImageTransformer")
    fP = os.path.expanduser(os.path.abspath(args.survey))
    with open(fP, "r") as fObj:
        survey = json.load(fObj)

    data = json.load(sys.stdin)
    tx = ImageTransformer(log, survey, data)
    path = tx.create_pdf(survey, data)
    images = list(tx.create_image_sequence(path, numberSeq=itertools.count()))
    index = tx.create_image_index(images)
    zipfile = tx.create_zip(images, index)
    sys.stdout.write(zipfile)
    return 0


def run():
    p = parser()
    args = p.parse_args()
    rv = main(args)
    sys.exit(rv)

if __name__ == "__main__":
    run()
