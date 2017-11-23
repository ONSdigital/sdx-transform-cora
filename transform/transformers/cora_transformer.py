import enum
import os.path
import re
from collections import OrderedDict
from io import StringIO

import dateutil.parser
from jinja2 import Environment, PackageLoader

from transform.settings import SDX_FTP_IMAGE_PATH, SDX_FTP_DATA_PATH, SDX_FTP_RECEIPT_PATH
from transform.transformers.image_transformer import ImageTransformer
from transform.transformers.pdf_transformer_style_cora import CoraPdfTransformerStyle

env = Environment(loader=PackageLoader('transform', 'templates'))


class CORATransformer:
    """
    This class captures our understanding of the agreed format
    of the UKIS survey.

    """

    _MAP_YN_10 = {
        'yes': '1',
        'no': '0',
    }

    _MAP_YN_01 = {
        'yes': '0',
        'no': '1',
    }

    _MAP_YN_21 = {
        'yes': '10',
        'no': '01',
    }

    _MAP_IMPORTANCE = {
        'not important': '0001',
        'low': '0010',
        'medium': '0100',
        'high': '1000',
    }

    _MAP_PROPORTIONS = {
        'none': '0001',
        'less than 40%': '0010',
        '40-90%': '0100',
        'over 90%': '1000',
    }

    class _Format(enum.Enum):

        zeroone = re.compile("^[01]{1}$")
        onetwo = re.compile("^[12]{1}$")
        twobin = re.compile("^[0-1]{1,2}$")
        twodigits = re.compile("^[0-9]{1,2}$")
        threedigits = re.compile("^[0-9]{1,3}$")
        sixdigits = re.compile("^[0-9]{1,6}$")
        sevendigits = re.compile("^[0-9]{1,7}$")
        onehotfour = re.compile("^(1000|0100|0010|0001|0000)$")
        yesno = re.compile("^yes|no$")
        yesnodk = re.compile("^yes|no|(don.+t know)$")

    class _Processor:

        @staticmethod
        def false(q, d):
            return "0"

        @staticmethod
        def checkbox(q, d):
            return '0' if q not in d else '1'

        @staticmethod
        def checkboxtwobit(q, d):
            return '00' if q not in d else '10'

        @staticmethod
        def radioyn10(q, d):
            return '0' if q not in d else CORATransformer._MAP_YN_10.get(
                d[q].lower(), '0'
            )

        @staticmethod
        def radioyn01(q, d):
            return '1' if q not in d else CORATransformer._MAP_YN_01.get(
                d[q].lower(), '1'
            )

        @staticmethod
        def radioyn21(q, d):
            return '00' if q not in d else CORATransformer._MAP_YN_21.get(
                d[q].lower(), '00'
            )

        @staticmethod
        def radioyndk(q, d):
            return '1' if d.get(q, "").lower() == "yes" else '0'

        @staticmethod
        def radioimportance(q, d):
            return '0000' if q not in d else CORATransformer._MAP_IMPORTANCE.get(
                d[q].lower(), '0000'
            )

        @staticmethod
        def radioproportion(q, d):
            return '0000' if q not in d else CORATransformer._MAP_PROPORTIONS.get(
                d[q].lower(), '0000'
            )

        @staticmethod
        def zeropadthree(q, d):
            return '' if q not in d else '{0:03d}'.format(int(d[q]))

        @staticmethod
        def zeropadtwo(q, d):
            return '' if q not in d else '{0:02d}'.format(int(d[q]))

        @staticmethod
        def dividebythousand(q, d):
            if q not in d:
                return ''
            if d[q].isdigit():
                return str(int(d[q]) // 1000)
            return ''

        @staticmethod
        def numbertype(q, d):
            return '' if q not in d else d[q]

        @staticmethod
        def comment(q, d):
            return '0' if q not in d else '1' if len(d[q].strip()) > 0 else '0'

    _defn = [
        (range(1, 4, 1), "0", _Format.zeroone, _Processor.false),
        (range(210, 250, 10), "0", _Format.zeroone, _Processor.checkbox),
        (range(410, 440, 10), "0", _Format.zeroone, _Processor.radioyn10),
        (range(2310, 2350, 10), "0", _Format.zeroone, _Processor.radioyn10),
        (range(1310, 1311, 1), "0", _Format.zeroone, _Processor.radioyn10),
        (range(2675, 2678, 1), "0", _Format.zeroone, _Processor.checkbox),
        (range(1410, 1411, 1), "", _Format.sixdigits, _Processor.dividebythousand),
        (range(1320, 1321, 1), "0", _Format.zeroone, _Processor.radioyn10),
        (range(1420, 1421, 1), "", _Format.sixdigits, _Processor.dividebythousand),
        (range(1331, 1334, 1), "0", _Format.zeroone, _Processor.checkbox),
        (range(1430, 1431, 1), "", _Format.sixdigits, _Processor.dividebythousand),
        (range(1340, 1341, 1), "0", _Format.zeroone, _Processor.radioyn10),
        (range(1440, 1441, 1), "", _Format.sixdigits, _Processor.dividebythousand),
        (range(1350, 1351, 1), "0", _Format.zeroone, _Processor.radioyn10),
        (range(1450, 1451, 1), "", _Format.sixdigits, _Processor.dividebythousand),
        (range(1360, 1361, 1), "0", _Format.zeroone, _Processor.radioyn10),
        (range(1460, 1461, 1), "", _Format.sixdigits, _Processor.dividebythousand),
        (range(1371, 1375, 1), "0", _Format.zeroone, _Processor.checkbox),
        (range(1470, 1471, 1), "", _Format.sixdigits, _Processor.dividebythousand),
        (range(510, 511, 1), "00", _Format.twobin, _Processor.radioyn21),
        (range(610, 640, 10), "0", _Format.zeroone, _Processor.checkbox),
        (range(520, 521, 1), "00", _Format.twobin, _Processor.radioyn21),
        (range(601, 604, 1), "0", _Format.zeroone, _Processor.checkbox),
        (range(710, 730, 10), "0", _Format.zeroone, _Processor.radioyn10),
        (range(810, 850, 10), "", _Format.threedigits, _Processor.zeropadthree),
        (range(900, 901, 1), "00", _Format.twobin, _Processor.radioyn21),
        (range(1010, 1040, 10), "0", _Format.zeroone, _Processor.checkbox),
        (range(1100, 1101, 1), "00", _Format.twobin, _Processor.radioyn21),
        (range(1510, 1540, 10), "0", _Format.zeroone, _Processor.radioyn10),
        (range(2657, 2668, 1), "0000", _Format.onehotfour, _Processor.radioimportance),
        (range(2011, 2012, 1), "0", _Format.zeroone, _Processor.checkbox),
        (range(2020, 2050, 10), "0", _Format.zeroone, _Processor.checkbox),
        (range(1210, 1212, 1), "0000", _Format.onehotfour, _Processor.radioimportance),
        (range(1220, 1300, 10), "0000", _Format.onehotfour, _Processor.radioimportance),
        (range(1212, 1214, 1), "0000", _Format.onehotfour, _Processor.radioimportance),
        (range(1601, 1602, 1), "0000", _Format.onehotfour, _Processor.radioimportance),
        (range(1620, 1621, 1), "0000", _Format.onehotfour, _Processor.radioimportance),
        (range(1610, 1612, 1), "0000", _Format.onehotfour, _Processor.radioimportance),
        (range(1631, 1633, 1), "0000", _Format.onehotfour, _Processor.radioimportance),
        (range(1640, 1700, 10), "0000", _Format.onehotfour, _Processor.radioimportance),
        (range(1811, 1815, 1), "00", _Format.twobin, _Processor.checkboxtwobit),
        (range(1821, 1825, 1), "00", _Format.twobin, _Processor.checkboxtwobit),
        (range(1881, 1885, 1), "00", _Format.twobin, _Processor.checkboxtwobit),
        (range(1891, 1895, 1), "00", _Format.twobin, _Processor.checkboxtwobit),
        (range(1841, 1845, 1), "00", _Format.twobin, _Processor.checkboxtwobit),
        (range(1851, 1855, 1), "00", _Format.twobin, _Processor.checkboxtwobit),
        (range(1861, 1865, 1), "00", _Format.twobin, _Processor.checkboxtwobit),
        (range(1871, 1875, 1), "00", _Format.twobin, _Processor.checkboxtwobit),
        (range(2650, 2657, 1), "0000", _Format.onehotfour, _Processor.radioproportion),
        (range(2668, 2671, 1), "0", _Format.zeroone, _Processor.radioyn10),
        (range(2672, 2674, 1), "0", _Format.zeroone, _Processor.radioyndk),
        (range(2410, 2430, 10), "", _Format.sixdigits, _Processor.dividebythousand),
        (range(2440, 2450, 10), "", _Format.sixdigits, _Processor.dividebythousand),
        (range(2510, 2530, 10), "", _Format.sevendigits, _Processor.numbertype),
        (range(2610, 2630, 10), "", _Format.threedigits, _Processor.zeropadthree),
        (range(2631, 2637, 1), "0", _Format.zeroone, _Processor.checkbox),
        (range(2678, 2679, 1), "0000", _Format.onehotfour, _Processor.radioimportance),
        (range(2700, 2701, 1), "0", _Format.zeroone, _Processor.comment),
        (range(2801, 2802, 1), "", _Format.threedigits, _Processor.numbertype),
        (range(2800, 2801, 1), "", _Format.twodigits, _Processor.zeropadtwo),
        (range(2900, 2901, 1), "00", _Format.twobin, _Processor.radioyn21),
    ]

    def __init__(self, logger, survey, response_data, sequence_no=1000):
        self._logger = logger
        self._survey = survey
        self._response = response_data
        self._sequence_no = sequence_no
        self._idbr = StringIO()
        self._tkn = StringIO()
        self.image_transformer = ImageTransformer(self._logger, self._survey, self._response,
                                                  CoraPdfTransformerStyle(), sequence_no=self._sequence_no,
                                                  base_image_path=SDX_FTP_IMAGE_PATH)
        self._setup_logger()

    def create_zip(self):
        """ Create a in memory zip from a renumbered sequence"""
        idbr_name = self._create_idbr()
        tkn_name = self._create_tkn()

        self.image_transformer.zip.append(os.path.join(SDX_FTP_DATA_PATH, tkn_name), self._tkn.read())
        self.image_transformer.zip.append(os.path.join(SDX_FTP_RECEIPT_PATH, idbr_name), self._idbr.read())

        self.image_transformer.get_zipped_images()
        self.image_transformer.zip.rewind()

    def get_zip(self):
        """Get access to the in memory zip """
        self.image_transformer.zip.rewind()
        return self.image_transformer.zip.in_memory_zip

    def _create_tkn(self):
        data = CORATransformer._transform(self._response["data"])
        output = CORATransformer._tkn_lines(
            surveyCode=self._response["survey_id"],
            ruRef=self._response["metadata"]["ru_ref"][:11],
            period=self._response["collection"]["period"],
            data=data
        )
        for row in output:
            self._tkn.write(row)
            self._tkn.write("\n")
        self._tkn.seek(0)
        tkn_name = "{0}_{1:04}".format(self._survey["survey_id"], self._sequence_no)
        return tkn_name

    def _create_idbr(self):
        template = env.get_template('idbr.tmpl')
        template_output = template.render(response=self._response)
        submission_date = dateutil.parser.parse(self._response['submitted_at'])
        submission_date_str = submission_date.strftime("%d%m")

        # Format is RECddMM_batchId.DAT
        # e.g. REC1001_30000.DAT for 10th January, batch 30000
        idbr_name = "REC%s_%04d.DAT" % (submission_date_str, self._sequence_no)
        self._idbr.write(template_output)
        self._idbr.seek(0)
        return idbr_name

    def _setup_logger(self):
        if self._survey:
            if 'metadata' in self._survey:
                metadata = self._survey['metadata']
                self._logger = self._logger.bind(
                    user_id=metadata['user_id'], ru_ref=metadata['ru_ref']
                )

            if 'tx_id' in self._survey:
                self.tx_id = self._survey['tx_id']
                self._logger = self._logger.bind(tx_id=self.tx_id)

    @staticmethod
    def _checks():
        """
        Returns a dictionary mapping question ids to field formats.

        """
        return OrderedDict([
            ("{0:04}".format(i), check)
            for rng, val, check, op in CORATransformer._defn
            for i in rng
        ])

    @staticmethod
    def _ops():
        """
        Returns a dictionary mapping question ids to field operations.

        """
        return OrderedDict([
            ("{0:04}".format(i), op)
            for rng, val, check, op in CORATransformer._defn
            for i in rng
        ])

    @staticmethod
    def _defaults():
        """
        Returns a dictionary mapping question ids to default values.
        """
        return OrderedDict([
            ("{0:04}".format(i), val)
            for rng, val, check, op in CORATransformer._defn
            for i in rng
        ])

    @staticmethod
    def _transform(data):
        rv = CORATransformer._defaults()
        ops = CORATransformer._ops()

        # Don't know generation
        if any(data.get(q, "").lower().endswith("t know") for q in ("2672", "2673")):
            rv["2674"] = "1"
        else:
            rv["2674"] = "0"

        for q in rv:

            if q == '10001':
                del rv[q]

            # Run the processors
            try:
                op = ops[q]
            except KeyError:
                continue
            else:
                rv[q] = op(q, data)

        # None-of-the-above generation
        if not any(rv.get(k) == "1" for k in ("0410", "0420", "0430")):
            rv["0440"] = "1"
        else:
            rv["0440"] = "0"

        if not any(rv.get(k) == "1" for k in ("2668", "2669", "2670")):
            rv["2671"] = "1"
        else:
            rv["2671"] = "0"

        return rv

    @staticmethod
    def _tkn_lines(surveyCode, ruRef, period, data):
        pageId = "1"
        questionInstance = "0"
        return [
            ":".join((surveyCode, ruRef, pageId, period, questionInstance, q, a))
            for q, a in data.items()
        ]
