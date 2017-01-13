from collections import OrderedDict
import itertools
import io
import json
import logging
import re
import tempfile
import unittest
import zipfile

import pkg_resources

from transform.transformers.CORATransformer import CORATransformer

from PyPDF2 import PdfFileReader

class Reference:

    check_yesno = re.compile("yes|no$")
    check_yesnodk = re.compile("yes|no|(don.+t know)$")
    check_twodigits = re.compile("[0-9]{2}$")
    check_threedigits = re.compile("[0-9]{3}$")
    check_sixdigits = re.compile("[0-9]{6}$")
    check_sevendigits = re.compile("[0-9]{7}$")
    check_zeroone = re.compile("[01]{1}$")
    check_onetwo = re.compile("[12]{1}$")
    check_onehotfour = re.compile("(0000|1000|0100|0010|0001)$")

    defn = [
        (range(210, 250, 10), "0", check_zeroone),
        (range(410, 450, 10), "0", check_zeroone),
        (range(2310, 2350, 10), "0", check_zeroone),
        (range(1310, 1311, 1), "0", check_zeroone),
        (range(2675, 2678, 10), "0", check_zeroone),
        (range(1410, 1411, 1), "", check_sixdigits),
        (range(1320, 1321, 1), "0", check_zeroone),
        (range(1420, 1421, 1), "", check_sixdigits),
        (range(1331, 1334, 1), "0", check_zeroone),
        (range(1430, 1431, 1), "", check_sixdigits),
        (range(1340, 1341, 1), "0", check_zeroone),
        (range(1440, 1441, 1), "", check_sixdigits),
        (range(1350, 1351, 1), "0", check_zeroone),
        (range(1450, 1451, 1), "", check_sixdigits),
        (range(1360, 1361, 1), "0", check_zeroone),
        (range(1460, 1461, 1), "", check_sixdigits),
        (range(1371, 1375, 1), "0", check_zeroone),
        (range(1470, 1471, 1), "", check_sixdigits),
        (range(510, 511, 1), "1", check_onetwo),
        (range(610, 640, 10), "0", check_zeroone),
        (range(520, 521, 1), "1", check_onetwo),
        (range(601, 604, 1), "0", check_zeroone),
        (range(710, 730, 10), "0", check_zeroone),
        (range(810, 850, 10), "", check_threedigits),
        (range(900, 901, 1), "0", check_zeroone),
        (range(1010, 1040, 10), "0", check_zeroone),
        (range(1100, 1101, 1), "0", check_zeroone),
        (range(1510, 1540, 10), "0", check_zeroone),
        (range(2657, 2668, 1), "0000", check_onehotfour),
        (range(2011, 2012, 1), "0", check_zeroone),
        (range(2020, 2050, 10), "0", check_zeroone),
        (range(1210, 1212, 1), "0000", check_onehotfour),
        (range(1220, 1300, 10), "0000", check_onehotfour),
        (range(1212, 1214, 1), "0000", check_onehotfour),
        (range(1601, 1602, 1), "0000", check_onehotfour),
        (range(1610, 1612, 1), "0000", check_onehotfour),
        (range(1631, 1632, 1), "0000", check_onehotfour),
        (range(1640, 1700, 10), "0000", check_onehotfour),
        (range(1811, 1815, 1), "0", check_zeroone),
        (range(1821, 1825, 1), "0", check_zeroone),
        (range(1881, 1885, 1), "0", check_zeroone),
        (range(1891, 1895, 1), "0", check_zeroone),
        (range(1841, 1845, 1), "0", check_zeroone),
        (range(1851, 1855, 1), "0", check_zeroone),
        (range(1861, 1865, 1), "0", check_zeroone),
        (range(1871, 1875, 1), "0", check_zeroone),
        (range(2650, 2657, 1), "0000", check_onehotfour),
        (range(2668, 2672, 1), "0", check_zeroone),
        (range(2672, 2675, 1), "0", check_zeroone),
        (range(2410, 2450, 10), "", check_sixdigits),
        (range(2510, 2530, 10), "", check_sevendigits),
        (range(2610, 2630, 10), "", check_threedigits),
        (range(2631, 2637, 1), "0", check_zeroone),
        (range(2700, 2701, 1), "0", check_zeroone),
        (range(2800, 2801, 1), "", check_threedigits),
        (range(2801, 2802, 1), "", check_twodigits),
        (range(2900, 2901, 1), "0", check_zeroone),
    ]


    @staticmethod
    def checks():
        return OrderedDict([
            ("{0:04}".format(i), check)
            for rng, val, check in Reference.defn
            for i in rng
        ])

    @staticmethod
    def defaults():
        return OrderedDict([
            ("{0:04}".format(i), val)
            for rng, val, check in Reference.defn
            for i in rng
        ])

    @staticmethod
    def transform(data):
        rv = Reference.defaults()
        rv.update(data)
        return rv

    def __init__(self, items=[]):
        self.obj = OrderedDict(items)

    def pack(self):
        rv = io.BytesIO()
        jobs = []
        with tempfile.TemporaryDirectory(dir="./tmp") as workspace:
            # Create files in workspace
            with zipfile.ZipFile(rv, "w", zipfile.ZIP_DEFLATED) as zipF:
                for src, dst in jobs:
                    fN = os.path.basename(src)
                    zipF.write(os.path.join(workspace, src), arcname=os.path.join(dst, fN))

        rv.seek(0)
        return rv

class CheckerTests(unittest.TestCase):

    def test_check_yesno(self):
        self.assertTrue(Reference.check_yesno.match("yes"))
        self.assertTrue(Reference.check_yesno.match("no"))
        self.assertFalse(Reference.check_yesno.match("don't know"))
        self.assertFalse(Reference.check_yesno.match("Yes"))
        self.assertFalse(Reference.check_yesno.match("No"))
        self.assertFalse(Reference.check_yesno.match("Don't know"))

    def test_check_yesnodk(self):
        self.assertTrue(Reference.check_yesnodk.match("yes"))
        self.assertTrue(Reference.check_yesnodk.match("no"))
        self.assertTrue(Reference.check_yesnodk.match("don't know"))
        self.assertFalse(Reference.check_yesnodk.match("Yes"))
        self.assertFalse(Reference.check_yesnodk.match("No"))
        self.assertFalse(Reference.check_yesnodk.match("Don't know"))

    def test_check_twodigits(self):
        self.assertTrue(Reference.check_twodigits.match("00"))
        self.assertTrue(Reference.check_twodigits.match("01"))
        self.assertTrue(Reference.check_twodigits.match("12"))
        self.assertTrue(Reference.check_twodigits.match("88"))
        self.assertFalse(Reference.check_twodigits.match(""))
        self.assertFalse(Reference.check_twodigits.match("0"))
        self.assertFalse(Reference.check_twodigits.match("000"))

    def test_check_threedigits(self):
        self.assertTrue(Reference.check_threedigits.match("001"))
        self.assertTrue(Reference.check_threedigits.match("012"))
        self.assertTrue(Reference.check_threedigits.match("123"))
        self.assertTrue(Reference.check_threedigits.match("456"))
        self.assertTrue(Reference.check_threedigits.match("789"))
        self.assertTrue(Reference.check_threedigits.match("890"))
        self.assertTrue(Reference.check_threedigits.match("900"))
        self.assertFalse(Reference.check_threedigits.match("01"))
        self.assertFalse(Reference.check_threedigits.match("12"))
        self.assertFalse(Reference.check_threedigits.match("0000"))
        self.assertFalse(Reference.check_threedigits.match("1234"))

    def test_check_sixdigits(self):
        self.assertTrue(Reference.check_sixdigits.match("000000"))
        self.assertTrue(Reference.check_sixdigits.match("000001"))
        self.assertTrue(Reference.check_sixdigits.match("012345"))
        self.assertTrue(Reference.check_sixdigits.match("678900"))
        self.assertFalse(Reference.check_sixdigits.match("00000"))
        self.assertFalse(Reference.check_sixdigits.match("0000000"))

    def test_check_sevendigits(self):
        self.assertTrue(Reference.check_sevendigits.match("0000000"))
        self.assertTrue(Reference.check_sevendigits.match("0000001"))
        self.assertTrue(Reference.check_sevendigits.match("0123456"))
        self.assertTrue(Reference.check_sevendigits.match("6789000"))
        self.assertFalse(Reference.check_sevendigits.match("000000"))
        self.assertFalse(Reference.check_sevendigits.match("00000000"))

    def test_check_zeroone(self):
        self.assertTrue(Reference.check_zeroone.match("0"))
        self.assertTrue(Reference.check_zeroone.match("1"))
        self.assertFalse(Reference.check_zeroone.match("2"))
        self.assertFalse(Reference.check_zeroone.match(""))

    def test_check_onetwo(self):
        self.assertTrue(Reference.check_onetwo.match("1"))
        self.assertTrue(Reference.check_onetwo.match("2"))
        self.assertFalse(Reference.check_onetwo.match("0"))
        self.assertFalse(Reference.check_onetwo.match(""))

    def test_definition_defaults(self):
        for ((k, c), (K, v)) in zip(Reference.checks().items(), Reference.defaults().items()):
            with self.subTest(k=k):
                self.assertEqual(k, K)
                if v:
                    self.assertTrue(c.match(v))
                elif c in (Reference.check_zeroone, Reference.check_onetwo):
                    # Empty string permitted for default values of numeric types only
                    self.fail(v)

class InterfaceTests(unittest.TestCase):

    def test_pack(self):
        ref = Reference()
        rv = ref.pack()
        with zipfile.ZipFile(rv, "r") as output:
            contents = output.infolist()

    def test_instantiation(self):
        data = json.loads(
            pkg_resources.resource_string(__name__, "replies/ukis-02.json").decode("utf-8")
        )
        tx = Reference(data.items())
        print(tx.obj)

class TransformTests(unittest.TestCase):

    def test_initial_defaults(self):
        ref = Reference.defaults()
        rv = Reference().transform({})
        self.assertEqual(len(ref), len(rv))

    def test_elimination(self):
        rv = Reference().transform({"10001": "No"})
        self.assertNotIn("10001", rv)

    def test_nine_digit_field_compression(self):
        keys = [k for k, v in Reference.checks().items() if v is Reference.check_sixdigits]
        for key in keys:
            with self.subTest(key=key):
                rv = Reference().transform({key: "123456789"})
                self.assertEqual("123456", rv[key])

    def test_none_of_the_above_generation(self):
        """
        None-of-the-above fields are generated when all of a group are 'No' or absent.

        """
        for grp, nota in [
            (("0410", "0420", "0430"), "0440"),
            (("2668", "2669", "2670"), "2671")
        ]:
            rv = Reference().transform({k: "Yes" for k in grp})
            self.assertEqual("0", rv[nota])
            rv = Reference().transform({k: "No" for k in grp})
            self.assertEqual("1", rv[nota])
            rv = Reference().transform({})
            self.assertEqual("1", rv[nota])

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
