from collections import OrderedDict
import itertools
import json
import logging
import os
from structlog import wrap_logger
import unittest
import pkg_resources

from PyPDF2 import PdfFileReader
from transform.transformers.cora_transformer import CORATransformer
from transform import settings
from unittest.mock import patch


class FormatTests(unittest.TestCase):
    """
    Checks the definitions of Format types.

    """

    def test_check_yesno(self):
        self.assertTrue(CORATransformer._Format.yesno.value.match("yes"))
        self.assertTrue(CORATransformer._Format.yesno.value.match("no"))
        self.assertFalse(CORATransformer._Format.yesno.value.match("don't know"))
        self.assertFalse(CORATransformer._Format.yesno.value.match("Yes"))
        self.assertFalse(CORATransformer._Format.yesno.value.match("No"))
        self.assertFalse(CORATransformer._Format.yesno.value.match("Don't know"))

    def test_check_yesnodk(self):
        self.assertTrue(CORATransformer._Format.yesnodk.value.match("yes"))
        self.assertTrue(CORATransformer._Format.yesnodk.value.match("no"))
        self.assertTrue(CORATransformer._Format.yesnodk.value.match("don't know"))
        self.assertFalse(CORATransformer._Format.yesnodk.value.match("Yes"))
        self.assertFalse(CORATransformer._Format.yesnodk.value.match("No"))
        self.assertFalse(CORATransformer._Format.yesnodk.value.match("Don't know"))

    def test_check_twodigits(self):
        """
        This field may be one or two digits long.

        """
        self.assertTrue(CORATransformer._Format.twodigits.value.match("0"))
        self.assertTrue(CORATransformer._Format.twodigits.value.match("00"))
        self.assertTrue(CORATransformer._Format.twodigits.value.match("01"))
        self.assertTrue(CORATransformer._Format.twodigits.value.match("12"))
        self.assertTrue(CORATransformer._Format.twodigits.value.match("88"))
        self.assertFalse(CORATransformer._Format.twodigits.value.match(""))
        self.assertFalse(CORATransformer._Format.twodigits.value.match("000"))

    def test_check_threedigits(self):
        """
        This field may be one to three digits long.

        """
        self.assertTrue(CORATransformer._Format.threedigits.value.match("0"))
        self.assertTrue(CORATransformer._Format.threedigits.value.match("1"))
        self.assertTrue(CORATransformer._Format.threedigits.value.match("01"))
        self.assertTrue(CORATransformer._Format.threedigits.value.match("12"))
        self.assertTrue(CORATransformer._Format.threedigits.value.match("001"))
        self.assertTrue(CORATransformer._Format.threedigits.value.match("012"))
        self.assertTrue(CORATransformer._Format.threedigits.value.match("123"))
        self.assertTrue(CORATransformer._Format.threedigits.value.match("456"))
        self.assertTrue(CORATransformer._Format.threedigits.value.match("789"))
        self.assertTrue(CORATransformer._Format.threedigits.value.match("890"))
        self.assertTrue(CORATransformer._Format.threedigits.value.match("900"))
        self.assertFalse(CORATransformer._Format.threedigits.value.match("0000"))
        self.assertFalse(CORATransformer._Format.threedigits.value.match("1234"))

    def test_check_sixdigits(self):
        """
        This field may be one to six digits long.

        """
        self.assertTrue(CORATransformer._Format.sixdigits.value.match("1"))
        self.assertTrue(CORATransformer._Format.sixdigits.value.match("12"))
        self.assertTrue(CORATransformer._Format.sixdigits.value.match("123"))
        self.assertTrue(CORATransformer._Format.sixdigits.value.match("1234"))
        self.assertTrue(CORATransformer._Format.sixdigits.value.match("12345"))
        self.assertTrue(CORATransformer._Format.sixdigits.value.match("123456"))
        self.assertTrue(CORATransformer._Format.sixdigits.value.match("000000"))
        self.assertTrue(CORATransformer._Format.sixdigits.value.match("678900"))
        self.assertFalse(CORATransformer._Format.sixdigits.value.match("1234567"))
        self.assertFalse(CORATransformer._Format.sixdigits.value.match("0000000"))

    def test_check_sevendigits(self):
        """
        This field may be one to seven digits long.

        """
        self.assertTrue(CORATransformer._Format.sevendigits.value.match("1"))
        self.assertTrue(CORATransformer._Format.sevendigits.value.match("12"))
        self.assertTrue(CORATransformer._Format.sevendigits.value.match("123"))
        self.assertTrue(CORATransformer._Format.sevendigits.value.match("1234"))
        self.assertTrue(CORATransformer._Format.sevendigits.value.match("12345"))
        self.assertTrue(CORATransformer._Format.sevendigits.value.match("123456"))
        self.assertTrue(CORATransformer._Format.sevendigits.value.match("1234567"))
        self.assertTrue(CORATransformer._Format.sevendigits.value.match("0000000"))
        self.assertTrue(CORATransformer._Format.sevendigits.value.match("8900000"))
        self.assertFalse(CORATransformer._Format.sevendigits.value.match("12345678"))
        self.assertFalse(CORATransformer._Format.sevendigits.value.match("00000000"))

    def test_check_zeroone(self):
        self.assertTrue(CORATransformer._Format.zeroone.value.match("0"))
        self.assertTrue(CORATransformer._Format.zeroone.value.match("1"))
        self.assertFalse(CORATransformer._Format.zeroone.value.match("2"))
        self.assertFalse(CORATransformer._Format.zeroone.value.match(""))

    def test_check_onetwo(self):
        self.assertTrue(CORATransformer._Format.onetwo.value.match("1"))
        self.assertTrue(CORATransformer._Format.onetwo.value.match("2"))
        self.assertFalse(CORATransformer._Format.onetwo.value.match("0"))
        self.assertFalse(CORATransformer._Format.onetwo.value.match(""))

    def test_definition_defaults(self):
        """
        Check all default values validate to their defined formats.

        """
        for ((k, c), (K, v)) in zip(CORATransformer._checks().items(), CORATransformer._defaults().items()):
            with self.subTest(k=k):
                self.assertEqual(k, K)
                if v:
                    self.assertTrue(c.value.match(v))
                elif c in (CORATransformer._Format.zeroone, CORATransformer._Format.onetwo):
                    # Empty string permitted for default values of numeric types only
                    self.fail(v)


class TransformTests(unittest.TestCase):

    def test_initial_defaults(self):
        """
        Check the generation of default values.

        Magic number accounts for fields inserted during transform.

        """
        ref = CORATransformer._defaults()
        rv = CORATransformer._transform({})
        self.assertEqual(len(ref) + 3, len(rv))

    def test_elimination(self):
        """
        Test that pure routing fields are removed.

        """
        rv = CORATransformer._transform({"10001": "No"})
        self.assertNotIn("10001", rv)
        rv = CORATransformer._transform({"10001": "Yes"})
        self.assertNotIn("10001", rv)

    def test_twobit_agree_operation(self):
        tickboxes = ["{0:04}".format(i) for rng in (
            range(1811, 1815, 1),
            range(1821, 1825, 1),
            range(1841, 1845, 1),
            range(1851, 1855, 1),
            range(1861, 1865, 1),
            range(1871, 1875, 1),
            range(1881, 1885, 1),
            range(1891, 1895, 1),
        ) for i in rng]
        for key in tickboxes:
            with self.subTest(key=key):
                rv = CORATransformer._transform({key: "Agreed answer"})
                self.assertEqual("10", rv[key])
                rv = CORATransformer._transform({})
                self.assertEqual("00", rv[key])

    def test_onezero_operation(self):
        """
        Supplied instructions suggest 0 maps to yes, 1 to no.

        """
        tickboxes = ["{0:04}".format(i) for rng in (
            range(210, 250, 10),
            range(2672, 2675, 1),
            range(2675, 2678, 1),
            range(1331, 1334, 1),
            range(1371, 1375, 1),
            range(610, 640, 10),
            range(601, 604, 1),
            range(1010, 1040, 10),
            range(1510, 1540, 1),
            range(1811, 1815, 1),
            range(1821, 1825, 1),
            range(1841, 1845, 1),
            range(1851, 1855, 1),
            range(1861, 1865, 1),
            range(1871, 1875, 1),
            range(1881, 1885, 1),
            range(1891, 1895, 1),
            range(2011, 2012, 1),
            range(2020, 2050, 10),
            range(2631, 2637, 1)
        ) for i in rng]
        keys = [
            k for k, v in CORATransformer._checks().items()
            if v is CORATransformer._Format.zeroone and k not in tickboxes and k != "2700"
        ]
        constants = ["0001", "0002", "0003"]
        inverts = ["0900", "1100", "2900"]
        for key in keys:
            with self.subTest(key=key):
                rv = CORATransformer._transform({key: "Yes"})
                if key in inverts or key in constants:
                    self.assertEqual("0", rv[key])
                if key not in ("0440", "2671"):  # None-of-the-above fields excluded
                    rv = CORATransformer._transform({key: "No"})
                    if key in inverts:
                        self.assertEqual("1", rv[key])
                    else:
                        self.assertEqual("0", rv[key])

    def test_onetwo_operation(self):
        keys = [
            k for k, v in CORATransformer._checks().items()
            if v is CORATransformer._Format.onetwo
        ]
        for key in keys:
            with self.subTest(key=key):
                rv = CORATransformer._transform({key: "Yes"})
                self.assertEqual("2", rv[key])
                rv = CORATransformer._transform({key: "No"})
                self.assertEqual("1", rv[key])

    def test_twobin_operation(self):
        tickboxes = ["{0:04}".format(i) for rng in (
            range(1811, 1815, 1),
            range(1821, 1825, 1),
            range(1841, 1845, 1),
            range(1851, 1855, 1),
            range(1861, 1865, 1),
            range(1871, 1875, 1),
            range(1881, 1885, 1),
            range(1891, 1895, 1),
        ) for i in rng]
        keys = [
            k for k, v in CORATransformer._checks().items()
            if v is CORATransformer._Format.twobin and k not in tickboxes
        ]
        for key in keys:
            with self.subTest(key=key):
                rv = CORATransformer._transform({})
                self.assertEqual("00", rv[key])
                rv = CORATransformer._transform({key: "Yes"})
                self.assertEqual("10", rv[key])
                rv = CORATransformer._transform({key: "No"})
                self.assertEqual("01", rv[key])

    def test_nine_digit_field_compression(self):
        """
        User enters a nine-digit field in £s for expenditure but downstream system
        expects multiples of £1000.

        """
        keys = [k for k, v in CORATransformer._checks().items() if v is CORATransformer._Format.sixdigits]
        for key in keys:
            with self.subTest(key=key):
                rv = CORATransformer._transform({key: "0"})
                self.assertEqual("0", rv[key])
                rv = CORATransformer._transform({key: "9"})
                self.assertEqual("0", rv[key])
                rv = CORATransformer._transform({key: "99"})
                self.assertEqual("0", rv[key])
                rv = CORATransformer._transform({key: "999"})
                self.assertEqual("0", rv[key])
                rv = CORATransformer._transform({key: "1234"})
                self.assertEqual("1", rv[key])
                rv = CORATransformer._transform({key: "12345"})
                self.assertEqual("12", rv[key])
                rv = CORATransformer._transform({key: "12999"})
                self.assertEqual("12", rv[key])
                rv = CORATransformer._transform({key: "123456"})
                self.assertEqual("123", rv[key])
                rv = CORATransformer._transform({key: "123999"})
                self.assertEqual("123", rv[key])
                rv = CORATransformer._transform({key: "1234567"})
                self.assertEqual("1234", rv[key])
                rv = CORATransformer._transform({key: "1234999"})
                self.assertEqual("1234", rv[key])
                rv = CORATransformer._transform({key: "12345432"})
                self.assertEqual("12345", rv[key])
                rv = CORATransformer._transform({key: "12345999"})
                self.assertEqual("12345", rv[key])
                rv = CORATransformer._transform({key: "123456000"})
                self.assertEqual("123456", rv[key])
                rv = CORATransformer._transform({key: "123456789"})
                self.assertEqual("123456", rv[key])

    def test_false(self):
        rv = CORATransformer._transform({})
        self.assertEqual("0", rv["0001"])
        self.assertEqual("0", rv["0002"])
        self.assertEqual("0", rv["0003"])

    def test_comment_removal(self):
        rv = CORATransformer._transform({"2700": ""})
        self.assertEqual("0", rv["2700"])
        rv = CORATransformer._transform({"2700": "Comment contains content"})
        self.assertEqual("1", rv["2700"])

    def test_none_of_the_above_generation(self):
        """
        None-of-the-above fields are generated when all of a group are 'No' or absent.

        """
        for grp, nota in [
            (("0410", "0420", "0430"), "0440"),
            (("2668", "2669", "2670"), "2671")
        ]:
            # Generate all possible combinations of input data.
            for data in itertools.product(
                ["No", "Yes", None], repeat=len(grp)
            ):
                # Construct input values; None means value absent.
                values = {k: v for k, v in zip(grp, data) if v is not None}
                with self.subTest(nota=nota, values=values):
                    rv = CORATransformer._transform(values)
                    if all(i in ("No", None) for i in data):
                        # None-of-the-above
                        self.assertTrue(all(rv[i] == "0" for i in grp))
                        self.assertEqual("1", rv[nota])
                    else:
                        # Standard translation of data
                        self.assertTrue(all(
                            rv[k] == ("1" if v == "Yes" else "0") for k, v in values.items()
                        ))
                        self.assertEqual("0", rv[nota])

    def test_dont_know_generation(self):
        """
        Don't-know fields are generated when any of a group are 'Don't know'.

        """
        for grp, dk in [
            (("2672", "2673"), "2674"),
        ]:
            # Generate all possible combinations of input data.
            for data in itertools.product(
                ["No", "Yes", "Don't know"], repeat=len(grp)
            ):
                # Construct input values.
                values = {k: v for k, v in zip(grp, data)}
                with self.subTest(dk=dk, values=values):
                    rv = CORATransformer._transform(values)
                    # Standard translation of data
                    self.assertTrue(all(
                        rv[k] == ("1" if v == "Yes" else "0") for k, v in zip(grp, data)
                    ))
                    if any(i == "Don't know" for i in values.values()):
                        self.assertEqual("1", rv[dk])
                    else:
                        self.assertEqual("0", rv[dk])


class OutputTests(unittest.TestCase):

    def test_tkn_formatting(self):
        items = [
            ("0510", "2"),
            ("0810", "123"),
            ("0820", "010"),
        ]
        expected = [
            "144:49900015425:1:201612:0:0510:2",
            "144:49900015425:1:201612:0:0810:123",
            "144:49900015425:1:201612:0:0820:010",
        ]
        rv = CORATransformer._tkn_lines(
            surveyCode="144", ruRef="49900015425", period="201612",
            data=OrderedDict(items)
        )
        self.assertEqual(expected, rv)


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
        self.settings = settings
        self.survey = json.loads(
            pkg_resources.resource_string(
                __name__, "../transform/surveys/144.0001.json"
            ).decode("utf-8")
        )
        self.data = json.loads(
            pkg_resources.resource_string(__name__, "replies/ukis-02.json").decode("utf-8")
        )

    @patch('transform.transformers.image_transformer.ImageTransformer._get_image_sequence_list',
           return_value=[1, 2])
    def test_ukis_pdf(self, mock_sequence_number):
        """
        Check that the correct questions appear in the generated image and that they all have
        answers.

        """
        temp_testfile = "testfile.pdf"
        log = wrap_logger(logging.getLogger(__name__))
        tx = CORATransformer(log, self.survey, self.data)
        tx.create_zip()
        with open(temp_testfile, "wb") as fp:
            fp.write(tx.image_transformer._pdf)

        pages = list(PackerTests.extract_text("testfile.pdf"))
        self.assertEqual(2, len(pages))
        questions = [
            ("3.3", "3.5", "3.8", "3.10", "3.12", "3.14", "3.17", "11.1"),
            ("11.2", "11.3", "13.1")
        ]
        for n, qs in enumerate(questions):
            for q in qs:
                with self.subTest(page=n, q=q):
                    pos = next((n for n, s in enumerate(pages[n]) if s.startswith(q)), None)
                    self.assertIsNotNone(pos)
                    try:
                        a = pages[n][pos + 1]
                    except IndexError:
                        # Question was last item of this page. Answer begins next one.
                        a = pages[n + 1][0]
                    # If answer is absent, we'll see the next question at this position.
                    self.assertFalse(any(a.startswith(i) for i in questions), "No answer in image.")

        self.assertIn("Respondent comment data.", pages[1])
        os.remove(temp_testfile)

    @unittest.skip("Sample Generation")
    def test_ukis_zip(self):
        log = logging.getLogger("test")
        tx = CORATransformer(log, self.survey, self.data)

        tx.create_zip()
        with open("sdx_to_cora-sample.zip", "w+b") as output:
            output.write(tx.get_zip())
