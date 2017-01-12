import itertools
import json
import logging
import unittest

import pkg_resources

from transform.transformers.CORATransformer import CORATransformer

from PyPDF2 import PdfFileReader

class UKISTests(unittest.TestCase):

    """
    SDX receives:
    2672=‘Yes|No|Don’t know’
    2673=‘Yes|No|Don’t know’

    The logic to convert into CORA would be something like:
    If 2672 == 'Yes' then 2672=1 else 2672=0
    If 2673 == 'Yes' then 2673=1 else 2673=0
    If 2672 == 'Don't know' or 2673 == ‘Don’t know’ then 2674=1 else 2674=0
    """

    @staticmethod
    def extract_text(path):
        with open(path, "rb") as content:
            pdf = PdfFileReader(content)
            for i in range(pdf.getNumPages()):
                page = pdf.getPage(i)
                strings = page.extractText()
                yield strings.splitlines()

    def setUp(self):
        self.survey = json.loads(
            pkg_resources.resource_string(
                __name__, "../transform/surveys/144.0001.json"
            ).decode("utf-8")
        )
        self.data = json.loads(
            pkg_resources.resource_string(__name__, "replies/ukis-01.json").decode("utf-8")
        )

    def test_ukis_base(self):
        log = logging.getLogger("test")
        tx = CORATransformer(log, self.survey, self.data)
        path = tx.create_pdf(self.survey, self.data)
        pages = list(UKISTests.extract_text(path))
        self.assertEqual(1, len(pages))
        self.assertIn("7.1 Any comments?", pages[0])
        "Respondent comment data."
        self.fail(pages)

    def test_ukis_zip(self):
        log = logging.getLogger("test")
        tx = CORATransformer(log, self.survey, self.data)
        path = tx.create_pdf(self.survey, self.data)
        images = list(tx.create_image_sequence(path, numberSeq=itertools.count()))
        index = tx.create_image_index(images)
        self.fail(index)
        zipfile = tx.create_zip(images, index)
