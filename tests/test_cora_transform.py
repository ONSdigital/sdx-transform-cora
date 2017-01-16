from collections import OrderedDict
import enum
import itertools
import io
import json
import logging
import os.path
import re
import tempfile
import unittest
import uuid
import zipfile

import pkg_resources

from transform.transformers.PDFTransformer import PDFTransformer
from transform.transformers.CORATransformer import CORATransformer

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate
from PyPDF2 import PdfFileReader


class Reference:
    """
    This class captures our understanding of the agreed format
    of the UKIS survey.

    It is used by the test fixture to automate tests and validate output.

    """

    class Format(enum.Enum):

        zeroone = re.compile("[01]{1}$")
        onetwo = re.compile("[12]{1}$")
        twodigits = re.compile("[0-9]{2}$")
        threedigits = re.compile("[0-9]{3}$")
        sixdigits = re.compile("[0-9]{6}$")
        sevendigits = re.compile("[0-9]{7}$")
        onehotfour = re.compile("(1000|0100|0010|0001)$")
        yesno = re.compile("yes|no$")
        yesnodk = re.compile("yes|no|(don.+t know)$")

    defn = [
        (range(210, 250, 10), "0", Format.zeroone),
        (range(410, 450, 10), "0", Format.zeroone),
        (range(2310, 2350, 10), "0", Format.zeroone),
        (range(1310, 1311, 1), "0", Format.zeroone),
        (range(2675, 2678, 10), "0", Format.zeroone),
        (range(1410, 1411, 1), "", Format.sixdigits),
        (range(1320, 1321, 1), "0", Format.zeroone),
        (range(1420, 1421, 1), "", Format.sixdigits),
        (range(1331, 1334, 1), "0", Format.zeroone),
        (range(1430, 1431, 1), "", Format.sixdigits),
        (range(1340, 1341, 1), "0", Format.zeroone),
        (range(1440, 1441, 1), "", Format.sixdigits),
        (range(1350, 1351, 1), "0", Format.zeroone),
        (range(1450, 1451, 1), "", Format.sixdigits),
        (range(1360, 1361, 1), "0", Format.zeroone),
        (range(1460, 1461, 1), "", Format.sixdigits),
        (range(1371, 1375, 1), "0", Format.zeroone),
        (range(1470, 1471, 1), "", Format.sixdigits),
        (range(510, 511, 1), "1", Format.onetwo),
        (range(610, 640, 10), "0", Format.zeroone),
        (range(520, 521, 1), "1", Format.onetwo),
        (range(601, 604, 1), "0", Format.zeroone),
        (range(710, 730, 10), "0", Format.zeroone),
        (range(810, 850, 10), "", Format.threedigits),
        (range(900, 901, 1), "0", Format.zeroone),
        (range(1010, 1040, 10), "0", Format.zeroone),
        (range(1100, 1101, 1), "0", Format.zeroone),
        (range(1510, 1540, 10), "0", Format.zeroone),
        (range(2657, 2668, 1), "1000", Format.onehotfour),
        (range(2011, 2012, 1), "0", Format.zeroone),
        (range(2020, 2050, 10), "0", Format.zeroone),
        (range(1210, 1212, 1), "1000", Format.onehotfour),
        (range(1220, 1300, 10), "1000", Format.onehotfour),
        (range(1212, 1214, 1), "1000", Format.onehotfour),
        (range(1601, 1602, 1), "1000", Format.onehotfour),
        (range(1620, 1621, 1), "1000", Format.onehotfour),
        (range(1610, 1612, 1), "1000", Format.onehotfour),
        (range(1631, 1633, 1), "1000", Format.onehotfour),
        (range(1640, 1700, 10), "1000", Format.onehotfour),
        (range(1811, 1815, 1), "0", Format.zeroone),
        (range(1821, 1825, 1), "0", Format.zeroone),
        (range(1881, 1885, 1), "0", Format.zeroone),
        (range(1891, 1895, 1), "0", Format.zeroone),
        (range(1841, 1845, 1), "0", Format.zeroone),
        (range(1851, 1855, 1), "0", Format.zeroone),
        (range(1861, 1865, 1), "0", Format.zeroone),
        (range(1871, 1875, 1), "0", Format.zeroone),
        (range(2650, 2657, 1), "1000", Format.onehotfour),
        (range(2668, 2672, 1), "0", Format.zeroone),
        (range(2672, 2675, 1), "0", Format.zeroone),
        (range(2410, 2430, 10), "", Format.sixdigits),
        (range(2440, 2450, 10), "", Format.sixdigits),
        (range(2510, 2530, 10), "", Format.sevendigits),
        (range(2610, 2630, 10), "", Format.threedigits),
        (range(2631, 2637, 1), "0", Format.zeroone),
        (range(2700, 2701, 1), "0", Format.zeroone),
        (range(2800, 2801, 1), "", Format.threedigits),
        (range(2801, 2802, 1), "", Format.twodigits),
        (range(2900, 2901, 1), "0", Format.zeroone),
    ]

    @staticmethod
    def checks():
        """
        Returns a dictionary mapping question ids to field formats.

        """
        return OrderedDict([
            ("{0:04}".format(i), check)
            for rng, val, check in Reference.defn
            for i in rng
        ])

    @staticmethod
    def defaults():
        """
        Returns a dictionary mapping question ids to default values.

        """
        return OrderedDict([
            ("{0:04}".format(i), val)
            for rng, val, check in Reference.defn
            for i in rng
        ])

    @staticmethod
    def transform(data):
        """
        This is a stub method which should be replaced by the 'transform' method
        of the implementation.

        """
        rv = Reference.defaults()
        rv.update(data)
        return rv

    def __init__(self, items=[]):
        self.obj = OrderedDict(items)

    def pack(self, survey={}):
        """
        Stub code used to generate typical output in absence of implementation.

        """
        survey = survey or json.loads(
            pkg_resources.resource_string(
                __name__, "../transform/surveys/144.0001.json"
            ).decode("utf-8")
        )

        rv = io.BytesIO()
        with tempfile.TemporaryDirectory(dir="./tmp") as workspace:
            name = uuid.uuid4().hex
            jobs = [
                (os.path.join(workspace, name + ".pdf"), name)
            ]
            p = PDFTransformer(survey, self.obj)
            doc = SimpleDocTemplate(jobs[0][0], pagesize=A4)
            doc.build(p.get_elements())

            # Create files in workspace
            with zipfile.ZipFile(rv, "w", zipfile.ZIP_DEFLATED) as zipF:
                for src, dst in jobs:
                    fN = os.path.basename(src)
                    zipF.write(src, arcname=os.path.join(dst, fN))

        rv.seek(0)
        return rv


class FormatTests(unittest.TestCase):
    """
    Checks the definitions of Format types.

    """

    def test_check_yesno(self):
        self.assertTrue(Reference.Format.yesno.value.match("yes"))
        self.assertTrue(Reference.Format.yesno.value.match("no"))
        self.assertFalse(Reference.Format.yesno.value.match("don't know"))
        self.assertFalse(Reference.Format.yesno.value.match("Yes"))
        self.assertFalse(Reference.Format.yesno.value.match("No"))
        self.assertFalse(Reference.Format.yesno.value.match("Don't know"))

    def test_check_yesnodk(self):
        self.assertTrue(Reference.Format.yesnodk.value.match("yes"))
        self.assertTrue(Reference.Format.yesnodk.value.match("no"))
        self.assertTrue(Reference.Format.yesnodk.value.match("don't know"))
        self.assertFalse(Reference.Format.yesnodk.value.match("Yes"))
        self.assertFalse(Reference.Format.yesnodk.value.match("No"))
        self.assertFalse(Reference.Format.yesnodk.value.match("Don't know"))

    def test_check_twodigits(self):
        self.assertTrue(Reference.Format.twodigits.value.match("00"))
        self.assertTrue(Reference.Format.twodigits.value.match("01"))
        self.assertTrue(Reference.Format.twodigits.value.match("12"))
        self.assertTrue(Reference.Format.twodigits.value.match("88"))
        self.assertFalse(Reference.Format.twodigits.value.match(""))
        self.assertFalse(Reference.Format.twodigits.value.match("0"))
        self.assertFalse(Reference.Format.twodigits.value.match("000"))

    def test_check_threedigits(self):
        self.assertTrue(Reference.Format.threedigits.value.match("001"))
        self.assertTrue(Reference.Format.threedigits.value.match("012"))
        self.assertTrue(Reference.Format.threedigits.value.match("123"))
        self.assertTrue(Reference.Format.threedigits.value.match("456"))
        self.assertTrue(Reference.Format.threedigits.value.match("789"))
        self.assertTrue(Reference.Format.threedigits.value.match("890"))
        self.assertTrue(Reference.Format.threedigits.value.match("900"))
        self.assertFalse(Reference.Format.threedigits.value.match("01"))
        self.assertFalse(Reference.Format.threedigits.value.match("12"))
        self.assertFalse(Reference.Format.threedigits.value.match("0000"))
        self.assertFalse(Reference.Format.threedigits.value.match("1234"))

    def test_check_sixdigits(self):
        self.assertTrue(Reference.Format.sixdigits.value.match("000000"))
        self.assertTrue(Reference.Format.sixdigits.value.match("000001"))
        self.assertTrue(Reference.Format.sixdigits.value.match("012345"))
        self.assertTrue(Reference.Format.sixdigits.value.match("678900"))
        self.assertFalse(Reference.Format.sixdigits.value.match("00000"))
        self.assertFalse(Reference.Format.sixdigits.value.match("0000000"))

    def test_check_sevendigits(self):
        self.assertTrue(Reference.Format.sevendigits.value.match("0000000"))
        self.assertTrue(Reference.Format.sevendigits.value.match("0000001"))
        self.assertTrue(Reference.Format.sevendigits.value.match("0123456"))
        self.assertTrue(Reference.Format.sevendigits.value.match("6789000"))
        self.assertFalse(Reference.Format.sevendigits.value.match("000000"))
        self.assertFalse(Reference.Format.sevendigits.value.match("00000000"))

    def test_check_zeroone(self):
        self.assertTrue(Reference.Format.zeroone.value.match("0"))
        self.assertTrue(Reference.Format.zeroone.value.match("1"))
        self.assertFalse(Reference.Format.zeroone.value.match("2"))
        self.assertFalse(Reference.Format.zeroone.value.match(""))

    def test_check_onetwo(self):
        self.assertTrue(Reference.Format.onetwo.value.match("1"))
        self.assertTrue(Reference.Format.onetwo.value.match("2"))
        self.assertFalse(Reference.Format.onetwo.value.match("0"))
        self.assertFalse(Reference.Format.onetwo.value.match(""))

    def test_definition_defaults(self):
        """
        Check all default values validate to their defined formats.

        """
        for ((k, c), (K, v)) in zip(Reference.checks().items(), Reference.defaults().items()):
            with self.subTest(k=k):
                self.assertEqual(k, K)
                if v:
                    self.assertTrue(c.value.match(v))
                elif c in (Reference.Format.zeroone, Reference.Format.onetwo):
                    # Empty string permitted for default values of numeric types only
                    self.fail(v)


class InterfaceTests(unittest.TestCase):
    """
    Temporary code for exercising zipfile creation.

    """

    def test_pack(self):
        data = json.loads(
            pkg_resources.resource_string(__name__, "replies/ukis-02.json").decode("utf-8")
        )
        ref = Reference(data.items())
        rv = ref.pack()
        with zipfile.ZipFile(rv, "r") as output:
            contents = output.infolist()
            self.assertTrue(contents)
            print(contents)


class TransformTests(unittest.TestCase):

    def test_initial_defaults(self):
        """
        Check the generation of default values.

        """
        ref = Reference.defaults()
        rv = Reference().transform({})
        self.assertEqual(len(ref), len(rv))

    def test_elimination(self):
        """
        Test that pure routing fields are removed.

        """
        rv = Reference().transform({"10001": "No"})
        self.assertNotIn("10001", rv)
        rv = Reference().transform({"10001": "Yes"})
        self.assertNotIn("10001", rv)

    def test_onezero_operation(self):
        keys = [k for k, v in Reference.checks().items() if v is Reference.Format.zeroone]
        for key in keys:
            with self.subTest(key=key):
                rv = Reference().transform({key: "No"})
                self.assertEqual("0", rv[key])
                rv = Reference().transform({key: "Yes"})
                self.assertEqual("1", rv[key])

    def test_nine_digit_field_compression(self):
        """
        User enters a nine-digit field in £s for expenditure but downstream system
        expects multiples of £1000.

        """
        keys = [k for k, v in Reference.checks().items() if v is Reference.Format.sixdigits]
        for key in keys:
            with self.subTest(key=key):
                rv = Reference().transform({key: "123456789"})
                self.assertEqual("123456", rv[key])

    def test_comment_removal(self):
        rv = Reference().transform({"2700": ""})
        self.assertEqual("0", rv["2700"])
        rv = Reference().transform({"2700": "Comment contains content"})
        self.assertEqual("1", rv["2700"])

    def test_none_of_the_above_generation(self):
        """
        None-of-the-above fields are generated when all of a group are 'No' or absent.

        """
        for grp, nota in [
            (("0410", "0420", "0430"), "0440"),
            (("2668", "2669", "2670"), "2671")
        ]:
            with self.subTest(nota=nota):
                rv = Reference().transform({k: "Yes" for k in grp})
                self.assertEqual("0", rv[nota])
                rv = Reference().transform({k: "No" for k in grp})
                self.assertEqual("1", rv[nota])
                rv = Reference().transform({})
                self.assertEqual("1", rv[nota])

    def test_dont_know_generation(self):
        """
        Don't-know fields are generated when any of a group are 'Don't know'.

        """
        for grp, dk in [
            (("2672", "2673"), "2674"),
        ]:
            with self.subTest(dk=dk):
                rv = Reference().transform({k: "Yes" for k in grp})
                self.assertTrue(all(rv[i] == "1" for i in grp))
                self.assertEqual("0", rv[dk])
                rv = Reference().transform({k: "No" for k in grp})
                self.assertTrue(all(rv[i] == "0" for i in grp))
                self.assertEqual("0", rv[dk])
                rv = Reference().transform({k: "Don't know" for k in grp})
                self.assertTrue(all(rv[i] == "0" for i in grp))
                self.assertEqual("1", rv[dk])


class PackerTests(unittest.TestCase):
    """
    Test image generation and zipfile creation.

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

    def test_ukis_pdf(self):
        """
        Check that the correct questions appear in the generated image and that they all have
        answers.

        """
        log = logging.getLogger("test")
        tx = CORATransformer(log, self.survey, self.data)
        path = tx.create_pdf(self.survey, self.data)
        pages = list(PackerTests.extract_text(path))
        self.assertEqual(2, len(pages))
        questions = ("2.4", "2.6", "2.9", "2.11", "2.13", "2.15", "2.18", "5.1", "5.2", "5.3")
        for q in questions:
            with self.subTest(q=q):
                pos = next((n for n, s in enumerate(pages[0]) if s.startswith(q)), None)
                self.assertIsNotNone(pos)
                try:
                    a = pages[0][pos + 1]
                except IndexError:
                    # Question was last item of this page. Answer begins next one.
                    a = pages[1][0]
                # If answer is absent, we'll see the next question at this position.
                self.assertFalse(any(a.startswith(i) for i in questions), "No answer in image.")

        self.assertIn("7.1 Any comments?", pages[1])
        self.assertIn("Respondent comment data.", pages[1])

    def test_ukis_zip(self):
        log = logging.getLogger("test")
        tx = CORATransformer(log, self.survey, self.data)
        path = tx.create_pdf(self.survey, self.data)
        images = list(tx.create_image_sequence(path, numberSeq=itertools.count()))
        index = tx.create_image_index(images)
        zipfile = tx.create_zip(images, index)
