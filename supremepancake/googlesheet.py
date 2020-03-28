"""Google Sheet module

See also:
    `gspread homepage <https://github.com/burnash/gspread>`_
    `gspread documentation <https://gspread.readthedocs.io/en/latest/>`_
"""

import logging

import gspread
from oauth2client.service_account import ServiceAccountCredentials


def open_sheet(credential_path: str,
               sheet_key: str) -> gspread.models.Spreadsheet:
    """Opens a Google Sheet"""
    logging.info('Opening sheet "%s" with credentials "%s"', sheet_key,
                 credential_path)
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        credential_path, ['https://spreadsheets.google.com/feeds'])
    client = gspread.authorize(credentials)
    return client.open_by_key(sheet_key)
