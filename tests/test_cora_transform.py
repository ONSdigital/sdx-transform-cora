from collections import OrderedDict
import itertools
import json
import logging
import unittest

import pkg_resources

from transform.transformers.CORATransformer import CORATransformer

from PyPDF2 import PdfFileReader

class Reference:

    defn = [
        (range(210, 250, 10), "0"),
        (range(410, 450, 10), "0"),
        (range(2310, 2350, 10), "0"),
        (range(1310, 1311, 1), "0"),
        (range(2675, 2678, 10), "0"),
        (range(1410, 1411, 1), ""),
        (range(1320, 1321, 1), "0"),
        (range(1420, 1421, 1), ""),
        (range(1331, 1334, 1), "0"),
        (range(1430, 1431, 1), ""),
        (range(1340, 1341, 1), "0"),
        (range(1440, 1441, 1), ""),
        (range(1350, 1351, 1), "0"),
        (range(1450, 1451, 1), ""),
        (range(1360, 1361, 1), "0"),
        (range(1460, 1461, 1), ""),
        (range(1371, 1375, 1), "0"),
        (range(1470, 1471, 1), ""),
        (range(510, 511, 1), "1"),
        (range(610, 640, 10), "0"),
        (range(520, 521, 1), "1"),
        (range(601, 604, 1), "0"),
        (range(710, 730, 10), "0"),
        (range(810, 850, 10), ""),
        (range(900, 901, 1), "0"),
        (range(1010, 1040, 10), "0"),
        (range(1100, 1101, 1), "0"),
        (range(1510, 1540, 10), "0"),
        (range(2657, 2668, 1), "0000"),
        (range(2011, 2012, 1), "0"),
        (range(2020, 2050, 10), "0"),
        (range(1210, 1212, 1), "0000"),
        (range(1220, 1300, 10), "0000"),
        (range(1212, 1214, 1), "0000"),
    ]

    @staticmethod
    def defaults():
        return OrderedDict([
            ("{0:04}".format(i), val)
            for rng, val in Reference.defn
            for i in rng
        ])

    def __call__(self, data):
        return {}

class TransformTests(unittest.TestCase):
    pass

    def test_boolean_defaults(self):
        tx = Reference()
        rv = tx.defaults()
        self.fail(json.dumps(rv, indent=0))

class PackerTests(unittest.TestCase):

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
            pkg_resources.resource_string(__name__, "replies/ukis-02.json").decode("utf-8")
        )

    def test_ukis_base(self):
        log = logging.getLogger("test")
        tx = CORATransformer(log, self.survey, self.data)
        path = tx.create_pdf(self.survey, self.data)
        pages = list(PackerTests.extract_text(path))
        self.assertEqual(1, len(pages))
        self.assertIn("7.1 Any comments?", pages[0])
        self.assertIn("Respondent comment data.", pages[0])

    def test_ukis_zip(self):
        log = logging.getLogger("test")
        tx = CORATransformer(log, self.survey, self.data)
        path = tx.create_pdf(self.survey, self.data)
        images = list(tx.create_image_sequence(path, numberSeq=itertools.count()))
        index = tx.create_image_index(images)
        zipfile = tx.create_zip(images, index)
