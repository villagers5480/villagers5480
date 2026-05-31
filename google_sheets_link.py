#!/usr/bin/env python3
"""Small CLI for linking this project to a Google Sheet.

The script authenticates with a Google service account and can read rows from or
append rows to a configured spreadsheet. Configuration is loaded from environment
variables, with optional support for a local .env file.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import os
import re
import sys
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

DEFAULT_RANGE = "Sheet1!A:Z"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID_PATTERN = re.compile(r"/spreadsheets/d/([a-zA-Z0-9-_]+)")
GOOGLE_SHEETS_HOME_URL = "https://docs.google.com/spreadsheets/u/2/?pli=1&ftv=1"


def load_dotenv_file() -> None:
    """Load optional local configuration from a .env file."""
    if importlib.util.find_spec("dotenv") is None:
        return

    from dotenv import load_dotenv

    load_dotenv()


def require_env(name: str) -> str:
    """Return a required environment variable or exit with a useful message."""
    value = os.getenv(name)
    if value:
        return value

    raise SystemExit(
        f"Missing {name}. Set it in your shell or add it to a local .env file."
    )


def extract_spreadsheet_id(sheet_reference: str) -> str:
    """Extract a spreadsheet ID from a Google Sheets URL or return a raw ID."""
    sheet_reference = sheet_reference.strip()
    if not sheet_reference:
        raise SystemExit("Google Sheet reference cannot be empty.")

    parsed_reference = urlparse(sheet_reference)
    if not parsed_reference.scheme and "/" not in sheet_reference:
        return sheet_reference

    match = SPREADSHEET_ID_PATTERN.search(parsed_reference.path)
    if match:
        return match.group(1)

    if parsed_reference.netloc == "docs.google.com" and parsed_reference.path.startswith(
        "/spreadsheets"
    ):
        raise SystemExit(
            "The Google Sheets URL does not include a spreadsheet ID. Open the "
            "specific sheet you want to connect and use a URL like "
            "https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit. "
            f"The provided Sheets home URL ({GOOGLE_SHEETS_HOME_URL}) cannot be "
            "used by the API because it points to the Sheets file picker, not one "
            "spreadsheet."
        )

    raise SystemExit(
        "Could not find a spreadsheet ID. Use GOOGLE_SHEET_ID with the raw ID or "
        "GOOGLE_SHEET_URL with a URL containing /spreadsheets/d/SPREADSHEET_ID/."
    )


def resolve_spreadsheet_id(sheet_id: str | None, sheet_url: str | None) -> str:
    """Resolve the spreadsheet ID from CLI args or environment variables."""
    if sheet_id:
        return extract_spreadsheet_id(sheet_id)
    if sheet_url:
        return extract_spreadsheet_id(sheet_url)

    env_sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if env_sheet_id:
        return extract_spreadsheet_id(env_sheet_id)

    env_sheet_url = os.getenv("GOOGLE_SHEET_URL")
    if env_sheet_url:
        return extract_spreadsheet_id(env_sheet_url)

    raise SystemExit(
        "Missing Google Sheet target. Set GOOGLE_SHEET_ID or GOOGLE_SHEET_URL, "
        "or pass --sheet-id/--sheet-url."
    )


def build_sheets_service(credentials_file: str):
    """Create an authenticated Google Sheets API service client."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    credentials_path = Path(credentials_file).expanduser()
    if not credentials_path.is_file():
        raise SystemExit(f"Service account file not found: {credentials_path}")

    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=SCOPES,
    )
    return build("sheets", "v4", credentials=credentials)


def read_rows(service, spreadsheet_id: str, range_name: str) -> list[list[str]]:
    """Read rows from a sheet range."""
    response = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_name)
        .execute()
    )
    return response.get("values", [])


def append_rows(
    service,
    spreadsheet_id: str,
    range_name: str,
    rows: Iterable[list[str]],
) -> dict:
    """Append rows to the configured sheet range."""
    body = {"values": list(rows)}
    return (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        )
        .execute()
    )


def rows_from_csv(csv_path: str) -> list[list[str]]:
    """Load rows from a CSV file for appending to a sheet."""
    path = Path(csv_path)
    if not path.is_file():
        raise SystemExit(f"CSV file not found: {path}")

    with path.open(newline="", encoding="utf-8") as csv_file:
        return [row for row in csv.reader(csv_file)]


def print_rows(rows: list[list[str]]) -> None:
    """Print rows as CSV so output can be piped into other tools."""
    writer = csv.writer(sys.stdout)
    writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read from or append to a Google Sheet using a service account.",
    )
    parser.add_argument(
        "--range",
        default=os.getenv("GOOGLE_SHEET_RANGE", DEFAULT_RANGE),
        help=f"A1 notation range to use. Defaults to {DEFAULT_RANGE!r}.",
    )
    parser.add_argument(
        "--sheet-id",
        help="Raw Google spreadsheet ID. Overrides GOOGLE_SHEET_ID/GOOGLE_SHEET_URL.",
    )
    parser.add_argument(
        "--sheet-url",
        help="Full Google Sheet URL containing /spreadsheets/d/SPREADSHEET_ID/.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("read", help="Read the configured range and print CSV.")

    append_parser = subparsers.add_parser("append", help="Append rows from a CSV file.")
    append_parser.add_argument("csv_file", help="Path to the CSV file to append.")

    return parser.parse_args()


def main() -> None:
    load_dotenv_file()
    args = parse_args()

    spreadsheet_id = resolve_spreadsheet_id(args.sheet_id, args.sheet_url)
    credentials_file = require_env("GOOGLE_SERVICE_ACCOUNT_FILE")
    service = build_sheets_service(credentials_file)

    if args.command == "read":
        print_rows(read_rows(service, spreadsheet_id, args.range))
        return

    if args.command == "append":
        rows = rows_from_csv(args.csv_file)
        if not rows:
            raise SystemExit(f"No rows found in CSV file: {args.csv_file}")
        response = append_rows(service, spreadsheet_id, args.range, rows)
        updated_range = response.get("updates", {}).get("updatedRange", args.range)
        print(f"Appended {len(rows)} row(s) to {updated_range}.")
        return

    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
