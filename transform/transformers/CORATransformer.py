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

    MAP_YN_10 = {
        'yes': '1',
        'no': '0',
    }

    MAP_YN_01 = {
        'yes': '0',
        'no': '1',
    }

    MAP_YN_21 = {
        'yes': '2',
        'no': '1',
    }

    MAP_IMPORTANCE = {
        'not important': '0001',
        'low': '0010',
        'medium': '0100',
        'high': '1000',
    }

    MAP_PROPORTIONS = {
        'none': '0001',
        'less than 40%': '0010',
        '40-90%': '0100',
        'over 90%': '1000',
    }

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

    class Processor:

        @staticmethod
        def checkbox(q, d):
            return '0' if q not in d else '1'

        @staticmethod
        def radioyn10(q, d):
            return '0' if q not in d else CORATransformer.MAP_YN_10[d[q].lower()]

        @staticmethod
        def radioyn01(q, d):
            return '1' if q not in d else CORATransformer.MAP_YN_01[d[q].lower()]

        @staticmethod
        def radioyn21(q, d):
            return '1' if q not in d else CORATransformer.MAP_YN_21[d[q].lower()]

        @staticmethod
        def radioimportance(q, d):
            return '0001' if q not in d else CORATransformer.MAP_IMPORTANCE[d[q].lower()]

        @staticmethod
        def radioproportion(q, d):
            return '0001' if q not in d else CORATransformer.MAP_PROPORTIONS[d[q].lower()]

        @staticmethod
        def zeropadthree(q, d):
            return '000' if q not in d else '{0:03d}'.format(int(d[q]))

        @staticmethod
        def zeropadtwo(q, d):
            return '00' if q not in d else '{0:02d}'.format(int(d[q]))

        # TODO: ask cora if this is correct formatting
        @staticmethod
        def thousandtruncate(q, d):
            return '' if q not in d else '{}{}'.format(d[q][:-3], '000')

        @staticmethod
        def numbertype(q, d):
            return '' if q not in d else d[q]

        @staticmethod
        def comment(q, d):
            return '0' if q not in d else '1' if len(d[q].strip()) > 0 else '0'

    defn = [
        (range(210, 250, 10), "0", Format.zeroone, Processor.checkbox),
        (range(410, 450, 10), "0", Format.zeroone, Processor.radioyn10),
        (range(2310, 2350, 10), "0", Format.zeroone, Processor.radioyn10),
        (range(1310, 1311, 1), "0", Format.zeroone, Processor.radioyn10),
        (range(2675, 2678, 1), "0", Format.zeroone, Processor.checkbox),
        (range(1410, 1411, 1), "", Format.sixdigits, Processor.thousandtruncate),
        (range(1320, 1321, 1), "0", Format.zeroone, Processor.radioyn10),
        (range(1420, 1421, 1), "", Format.sixdigits, Processor.thousandtruncate),
        (range(1331, 1334, 1), "0", Format.zeroone, Processor.checkbox),
        (range(1430, 1431, 1), "", Format.sixdigits, Processor.thousandtruncate),
        (range(1340, 1341, 1), "0", Format.zeroone, Processor.radioyn10),
        (range(1440, 1441, 1), "", Format.sixdigits, Processor.thousandtruncate),
        (range(1350, 1351, 1), "0", Format.zeroone, Processor.radioyn10),
        (range(1450, 1451, 1), "", Format.sixdigits, Processor.thousandtruncate),
        (range(1360, 1361, 1), "0", Format.zeroone, Processor.radioyn10),
        (range(1460, 1461, 1), "", Format.sixdigits, Processor.thousandtruncate),
        (range(1371, 1375, 1), "0", Format.zeroone, Processor.checkbox),
        (range(1470, 1471, 1), "", Format.sixdigits, Processor.thousandtruncate),
        (range(510, 511, 1), "1", Format.onetwo, Processor.radioyn21),
        (range(610, 640, 10), "0", Format.zeroone, Processor.checkbox),
        (range(520, 521, 1), "1", Format.onetwo, Processor.radioyn21),
        (range(601, 604, 1), "0", Format.zeroone, Processor.checkbox),
        (range(710, 730, 10), "0", Format.zeroone, Processor.radioyn10),
        (range(810, 850, 10), "", Format.threedigits, Processor.zeropadthree),
        (range(900, 901, 1), "0", Format.zeroone, Processor.radioyn01),
        (range(1010, 1040, 10), "0", Format.zeroone, Processor.checkbox),
        (range(1100, 1101, 1), "0", Format.zeroone, Processor.radioyn01),
        (range(1510, 1540, 10), "0", Format.zeroone, Processor.checkbox),
        (range(2657, 2668, 1), "1000", Format.onehotfour, Processor.radioimportance),
        (range(2011, 2012, 1), "0", Format.zeroone, Processor.checkbox),
        (range(2020, 2050, 10), "0", Format.zeroone, Processor.checkbox),
        (range(1210, 1212, 1), "1000", Format.onehotfour, Processor.radioimportance),
        (range(1220, 1300, 10), "1000", Format.onehotfour, Processor.radioimportance),
        (range(1212, 1214, 1), "1000", Format.onehotfour, Processor.radioimportance),
        (range(1601, 1602, 1), "1000", Format.onehotfour, Processor.radioimportance),
        (range(1620, 1621, 1), "1000", Format.onehotfour, Processor.radioimportance),
        (range(1610, 1612, 1), "1000", Format.onehotfour, Processor.radioimportance),
        (range(1631, 1633, 1), "1000", Format.onehotfour, Processor.radioimportance),
        (range(1640, 1700, 10), "1000", Format.onehotfour, Processor.radioimportance),
        (range(1811, 1815, 1), "0", Format.zeroone, Processor.checkbox),
        (range(1821, 1825, 1), "0", Format.zeroone, Processor.checkbox),
        (range(1881, 1885, 1), "0", Format.zeroone, Processor.checkbox),
        (range(1891, 1895, 1), "0", Format.zeroone, Processor.checkbox),
        (range(1841, 1845, 1), "0", Format.zeroone, Processor.checkbox),
        (range(1851, 1855, 1), "0", Format.zeroone, Processor.checkbox),
        (range(1861, 1865, 1), "0", Format.zeroone, Processor.checkbox),
        (range(1871, 1875, 1), "0", Format.zeroone, Processor.checkbox),
        (range(2650, 2657, 1), "1000", Format.onehotfour, Processor.radioimportance),
        (range(2668, 2672, 1), "0", Format.zeroone, Processor.radioyn10),
        (range(2672, 2675, 1), "0", Format.zeroone, Processor.radioyn10),
        (range(2410, 2430, 10), "", Format.sixdigits, Processor.thousandtruncate),
        (range(2440, 2450, 10), "", Format.sixdigits, Processor.thousandtruncate),
        (range(2510, 2530, 10), "", Format.sevendigits, Processor.numbertype),
        (range(2610, 2630, 10), "", Format.threedigits, Processor.zeropadthree),
        (range(2631, 2637, 1), "0", Format.zeroone, Processor.checkbox),
        (range(2700, 2701, 1), "0", Format.zeroone, Processor.comment),
        (range(2800, 2801, 1), "", Format.threedigits, Processor.zeropadthree),
        (range(2801, 2802, 1), "", Format.twodigits, Processor.zeropadtwo),
        (range(2900, 2901, 1), "0", Format.zeroone, Processor.radioyn01),
    ]

    @staticmethod
    def checks():
        """
        Returns a dictionary mapping question ids to field formats.

        """
        return OrderedDict([
            ("{0:04}".format(i), check)
            for rng, val, check, op in CORATransformer.defn
            for i in rng
        ])

    @staticmethod
    def ops():
        """
        Returns a dictionary mapping question ids to field operations.

        """
        return OrderedDict([
            ("{0:04}".format(i), op)
            for rng, val, check, op in CORATransformer.defn
            for i in rng
        ])

    @staticmethod
    def defaults():
        """
        Returns a dictionary mapping question ids to default values.

        """
        return OrderedDict([
            ("{0:04}".format(i), val)
            for rng, val, check, op in CORATransformer.defn
            for i in rng
        ])

    @staticmethod
    def transform(data):
        defaults = CORATransformer.defaults()
        ops = CORATransformer.ops()
        rv = OrderedDict()

        for q in ops:

            # === START SPECIAL CASES
            if q == '0440':
                rv[q] = '0' if "yes" in [val.lower() for q, val in data.items() if q in [
                    '0410', '0420', '0430',
                ] and val.lower() == "yes"] else '1'
                continue

            if q == '2671':
                rv[q] = '0' if "yes" in [val.lower() for q, val in data.items() if q in [
                    '2668', '2669', '2670',
                ] and val.lower() == "yes"] else '1'
                continue

            if q == '2674':
                rv[q] = '1' if "Don't know" in [val for q, val in data.items() if q in [
                    '2672', '2673',
                ] and val == "Don't know"] else '0'
                continue
            # === END SPECIAL CASES

            # run the processors:
            try:
                rv[q] = ops[q](q, data)
            except KeyError:
                rv[q] = defaults[q]

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
