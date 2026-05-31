import os
import unittest
from unittest.mock import patch

from google_sheets_link import (
    GOOGLE_SHEETS_HOME_URL,
    extract_spreadsheet_id,
    resolve_spreadsheet_id,
)


class GoogleSheetsLinkTests(unittest.TestCase):
    def test_extracts_id_from_full_sheet_url(self):
        sheet_id = "abc123_DEF-456"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"

        self.assertEqual(extract_spreadsheet_id(url), sheet_id)

    def test_accepts_raw_spreadsheet_id(self):
        self.assertEqual(extract_spreadsheet_id("abc123_DEF-456"), "abc123_DEF-456")

    def test_rejects_google_sheets_home_url(self):
        with self.assertRaisesRegex(SystemExit, "does not include a spreadsheet ID"):
            extract_spreadsheet_id(GOOGLE_SHEETS_HOME_URL)

    def test_resolves_google_sheet_url_environment_variable(self):
        sheet_id = "abc123_DEF-456"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

        with patch.dict(os.environ, {"GOOGLE_SHEET_URL": url}, clear=True):
            self.assertEqual(resolve_spreadsheet_id(None, None), sheet_id)

    def test_sheet_id_argument_overrides_environment_url(self):
        with patch.dict(
            os.environ,
            {"GOOGLE_SHEET_URL": "https://docs.google.com/spreadsheets/d/from_env/edit"},
            clear=True,
        ):
            self.assertEqual(resolve_spreadsheet_id("from_argument", None), "from_argument")


if __name__ == "__main__":
    unittest.main()
