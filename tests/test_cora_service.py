from transform import app
from tests.test_views import test_message
import unittest
import io
import zipfile


class TestCoraTransformService(unittest.TestCase):

    transformEndpoint = "/cora"

    def setUp(self):

        # creates a test client
        self.app = app.test_client()

        # propagate the exceptions to the test client
        self.app.testing = True

    def get_zip_list(self, endpoint):

        r = self.app.post(endpoint, data=test_message)

        zip_contents = io.BytesIO(r.data)

        z = zipfile.ZipFile(zip_contents)
        z.close()

        return z.namelist()

    def test_invalid_data(self):
        r = self.app.post(self.transformEndpoint, data="rubbish")

        self.assertEqual(r.status_code, 400)
