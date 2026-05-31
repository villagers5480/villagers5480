# Villagers5480 Google Sheets Link

This repository now includes a small Python command-line tool for linking the
project to a Google Sheet. It uses a Google Cloud service account so the script
can read from and append to a spreadsheet without requiring an interactive OAuth
login.

## What was added

- `google_sheets_link.py` — a CLI that can read Google Sheet rows as CSV or
  append rows from a CSV file.
- `requirements.txt` — Python dependencies for the Google Sheets API client.
- `.gitignore` — ignores local virtual environments, `.env` files, and service
  account credential JSON files.

## Setup

1. Create or choose a Google Cloud project.
2. Enable the Google Sheets API for that project.
3. Create a service account and download its JSON key file.
4. Share the target Google Sheet with the service account email address. The
   service account needs viewer access for `read` and editor access for
   `append`.
5. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

6. Create a local `.env` file, or export these variables in your shell. You
   can use either `GOOGLE_SHEET_ID` or `GOOGLE_SHEET_URL` for the target sheet:

   ```bash
   GOOGLE_SERVICE_ACCOUNT_FILE=/absolute/path/to/service-account.json
   GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/your_spreadsheet_id/edit
   GOOGLE_SHEET_RANGE=Sheet1!A:Z
   ```

The spreadsheet ID is the long value in a Google Sheets URL between `/d/` and
`/edit`. A link such as
`https://docs.google.com/spreadsheets/u/2/?pli=1&ftv=1` opens the Google Sheets
home/file picker and does not identify one spreadsheet, so it cannot be used by
the API. Open the actual sheet first, then copy the URL that contains
`/spreadsheets/d/.../edit`.

## Usage

Read rows from the configured range and print them as CSV:

```bash
python google_sheets_link.py read
```

Append rows from a CSV file:

```bash
python google_sheets_link.py append path/to/rows.csv
```

Use a different range for a single command:

```bash
python google_sheets_link.py --range 'Sheet2!A:C' read
```

Pass a specific sheet URL for a single command:

```bash
python google_sheets_link.py --sheet-url 'https://docs.google.com/spreadsheets/d/your_spreadsheet_id/edit' read
```

## Security notes

- Do not commit service account JSON keys or `.env` files.
- Keep the Google Sheet shared only with identities that need access.
- Prefer a dedicated service account for this project rather than reusing a
  broad-access account.
