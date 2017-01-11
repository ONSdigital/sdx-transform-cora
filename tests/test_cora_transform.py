import json
import unittest

import pkg_resources


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

    def setUp(self):
        self.data = json.loads(
            pkg_resources.resource_string(__name__, "replies/ukis-01.json").decode("utf-8")
        )

    def test_ukis_base(self):
        print(__name__)
        print(self.data)
