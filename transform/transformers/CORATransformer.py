#!/usr/bin/env python
#   coding: UTF-8

from collections import OrderedDict
import enum
import os.path
import re
import sys

from transform.transformers.CSTransformer import CSTransformer
from transform.transformers.ImageTransformer import ImageTransformer
from transform.transformers.PDFTransformer import PDFTransformer


class CORATransformer(CSTransformer, ImageTransformer):
    """
    This class captures our understanding of the agreed format
    of the UKIS survey.

    """

    class Format(enum.Enum):

        zeroone = re.compile("^[01]{1}$")
        onetwo = re.compile("^[12]{1}$")
        twodigits = re.compile("^[0-9]{1,2}$")
        threedigits = re.compile("^[0-9]{1,3}$")
        sixdigits = re.compile("^[0-9]{1,6}$")
        sevendigits = re.compile("^[0-9]{1,7}$")
        onehotfour = re.compile("^(1000|0100|0010|0001)$")
        yesno = re.compile("^yes|no$")
        yesnodk = re.compile("^yes|no|(don.+t know)$")

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
            for rng, val, check in CORATransformer.defn
            for i in rng
        ])

    @staticmethod
    def defaults():
        """
        Returns a dictionary mapping question ids to default values.

        """
        return OrderedDict([
            ("{0:04}".format(i), val)
            for rng, val, check in CORATransformer.defn
            for i in rng
        ])

    @staticmethod
    def transform(data):
        rv = CORATransformer.defaults()

        ops = {
            CORATransformer.Format.zeroone: lambda x: "1" if x == "Yes" else "0",
            CORATransformer.Format.onetwo: lambda x: "2" if x == "Yes" else "1",
            CORATransformer.Format.twodigits: (
                lambda x: x if CORATransformer.Format.twodigits.value.match(x) else ""
            ),
            CORATransformer.Format.threedigits: (
                lambda x: x if CORATransformer.Format.threedigits.value.match(x) else ""
            ),
            CORATransformer.Format.onehotfour: (
                lambda x: x if CORATransformer.Format.onehotfour.value.match(x) else ""
            ),
            CORATransformer.Format.sixdigits: (
                lambda x: str(int(x) // 1000) if x.isdigit() else ""
            ),
            CORATransformer.Format.sevendigits: (
                lambda x: x if CORATransformer.Format.sevendigits.value.match(x) else ""
            ),
        }

        checks = CORATransformer.checks()
        for k, v in data.items():

            # Eliminate routing fields
            if k == "10001":
                continue

            # Remove comment data
            elif k == "2700":
                rv[k] = "1" if v else "0"
                continue

            # Don't know generation
            elif k in ("2672", "2673") and v == "Don't know":
                rv["2674"] = "1"

            # Validate and transform by type
            fmt = checks.get(k)
            op = ops.get(fmt, str)
            rv[k] = op(v)

        # None-of-the-above generation
        if not any(rv[k] == "1" for k in ("0410", "0420", "0430")):
            rv["0440"] = "1"

        if not any(rv[k] == "1" for k in ("2668", "2669", "2670")):
            rv["2671"] = "1"

        return rv

    @staticmethod
    def tkn_lines(surveyCode, ruRef, period, data):
        pageId = "1"
        questionInstance = "0"
        return [
            ":".join((surveyCode, ruRef, pageId, period, questionInstance, q, a))
            for q, a in data.items()
        ]

    @staticmethod
    def create_pdf(survey, data):
        '''
        Create a pdf which will be used as the basis for images
        '''
        pdf_transformer = PDFTransformer(survey, data)
        return pdf_transformer.render_to_file()

    def create_zip(self):
        return CSTransformer.create_zip(self)

    def prepare_archive(self):
        super().prepare_archive()

        fN = "{0}_{1:04}".format(self.survey["survey_id"], self.sequence_no)
        fP = os.path.join(self.path, fN)
        with open(fP, "w") as tkn:
            data = CORATransformer.transform(self.response["data"])
            output = CORATransformer.tkn_lines(
                surveyCode=self.response["survey_id"],
                ruRef=self.response["metadata"]["ru_ref"],
                period=self.response["collection"]["period"],
                data=data
            )
            tkn.write("\n".join(output))
            self.files_to_archive.insert(0, ("EDC_QData", fN))


def run():
    print("CLI not implemented.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    run()
