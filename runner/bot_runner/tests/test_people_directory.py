import os
import unittest
from unittest.mock import patch

from services.people_directory import PeopleDirectoryService


class PeopleDirectoryCredentialsTests(unittest.TestCase):
    def test_runner_credentials_are_used_when_source_has_no_credentials(self):
        source = {"url": "https://docs.google.com/example"}

        with patch.dict(os.environ, {"KEEPCAT_CREDENTIALS_BASE64": "runner-secret"}):
            value = PeopleDirectoryService._service_account_b64(source)

        self.assertEqual(value, "runner-secret")

    def test_source_credentials_have_priority(self):
        source = {"service_account_b64": "source-secret"}

        with patch.dict(os.environ, {"KEEPCAT_CREDENTIALS_BASE64": "runner-secret"}):
            value = PeopleDirectoryService._service_account_b64(source)

        self.assertEqual(value, "source-secret")


if __name__ == "__main__":
    unittest.main()
