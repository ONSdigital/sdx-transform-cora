from transform import app
from transform.views.test_views import test_message
import unittest
import io
import json
import zipfile
from unittest.mock import patch


class TestCoraTransformService(unittest.TestCase):

    transformEndpoint = "/cora"

    def setUp(self):

        # creates a test client
        self.app = app.test_client()

        # propagate the exceptions to the test client
        self.app.testing = True

    def get_zip_file_contents(self, endpoint, msg_data=test_message):
        response = self.app.post(endpoint, data=msg_data)
        return io.BytesIO(response.data)

    def get_zip_list(self, endpoint):
        zip_contents = self.get_zip_file_contents(endpoint)
        z = zipfile.ZipFile(zip_contents)
        z.close()

        return z.namelist()

    @patch('transform.transformers.image_transformer.ImageTransformer._get_image_sequence_list', return_value=[13, 14])
    def test_creates_cora_defaults(self, mock_sequence_no):

        ziplist = self.get_zip_list(self.transformEndpoint)

        # Check that all expected contents are listed in the zip
        expected = [
            'EDC_QData/144_1000',
            'EDC_QReceipts/REC1203_1000.DAT',
            'EDC_QImages/Images/S000000013.JPG',
            'EDC_QImages/Images/S000000014.JPG',
            'EDC_QImages/Index/EDC_144_20160312_1000.csv',
            'EDC_QJson/144_1000.json'
        ]

        self.assertEqual(expected, ziplist)

    @patch('transform.transformers.image_transformer.ImageTransformer._get_image_sequence_list', return_value=[1985, 1986])
    def test_creates_cora_sequence(self, mock_sequence_no):

        ziplist = self.get_zip_list(self.transformEndpoint + "/2345")

        # Check that all expected contents are listed in the zip
        expected = [
            'EDC_QData/144_2345',
            'EDC_QReceipts/REC1203_2345.DAT',
            'EDC_QImages/Images/S000001985.JPG',
            'EDC_QImages/Images/S000001986.JPG',
            'EDC_QImages/Index/EDC_144_20160312_2345.csv',
            'EDC_QJson/144_2345.json'
        ]

        self.assertEqual(expected, ziplist)

        ziplist = self.get_zip_list(self.transformEndpoint + "/999")

        # Check that all expected contents are listed in the zip
        expected = [
            'EDC_QData/144_0999',
            'EDC_QReceipts/REC1203_0999.DAT',
            'EDC_QImages/Images/S000001985.JPG',
            'EDC_QImages/Images/S000001986.JPG',
            'EDC_QImages/Index/EDC_144_20160312_0999.csv',
            'EDC_QJson/144_0999.json'
        ]

        self.assertEqual(expected, ziplist)

    @patch('transform.transformers.ImageTransformer._get_image_sequence_list', return_value=[13, 14])
    def test_original_json_stored_in_zip(self, mock_sequence_no):
        """Compare the dictionary loaded from the zip file json is the same as that submitted"""
        expected_json_data = json.loads(test_message)

        zip_contents = self.get_zip_file_contents(self.transformEndpoint + "/2345")

        z = zipfile.ZipFile(zip_contents)
        zfile = z.open('EDC_QJson/144_2345.json', 'r')
        actual_json_data = json.loads(zfile.read().decode('utf-8'))

        self.assertEquals(actual_json_data, expected_json_data)

    def test_invalid_data(self):
        r = self.app.post(self.transformEndpoint, data="rubbish")

        self.assertEqual(r.status_code, 400)
