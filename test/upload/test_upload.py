import os
import shutil
import unittest
from unittest import mock

from starlette.testclient import TestClient

import src.main as main
from src.main import TEMP_FOLDER

TEST_DATASET_PATH = "datasets/test_data.csv"


class MockGenerateResponse:
    def __init__(self, text):
        self.text = text


app = main.app
client = TestClient(app)


class UploadTestCase(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEMP_FOLDER):
            shutil.rmtree(TEMP_FOLDER)
        os.makedirs(TEMP_FOLDER)

    @mock.patch.object(main, 'get_genai_summary')
    def test_something(self, mock_get_genai_summary):
        mock_get_genai_summary.return_value = MockGenerateResponse("Test response.")

        with open(TEST_DATASET_PATH, mode="rb") as f:
            actual = client.post("/upload-csv", files={"file": f}).json()
            print(actual)
            self.assertEqual(actual["filename"], "test_data.csv")
            self.assertEqual(actual["data"],
                             [dict(id=1, item_name="Plush", price=79.99), dict(id=2, item_name="Box", price=120)])
            self.assertEqual(actual["summary"], "Test response.")


if __name__ == '__main__':
    unittest.main()
