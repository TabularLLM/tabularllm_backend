import os
import shutil
import unittest
from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient

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

    def test_upload(self):
        with (
            patch('src.main.get_genai_summary', return_value=MockGenerateResponse("Test response."))
        ):
            with open(TEST_DATASET_PATH, mode="rb") as f:
                actual = client.post("/upload-csv", files={"file": f})
                actual_body = actual.json()
                print(actual_body)
                self.assertEqual(actual.status_code, status.HTTP_200_OK)
                self.assertEqual(os.path.basename(TEST_DATASET_PATH), actual_body["filename"])
                self.assertEqual([dict(id=1, item_name="Plush", price=79.99), dict(id=2, item_name="Box", price=120)],
                                 actual_body["data"])
                self.assertEqual(actual_body["summary"], "Test response.")


if __name__ == '__main__':
    unittest.main()
