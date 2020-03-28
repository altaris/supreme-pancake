"""Google Sheet module

See also:
    `gspread homepage <https://github.com/burnash/gspread>`_
    `gspread documentation <https://gspread.readthedocs.io/en/latest/>`_
"""

import logging
from typing import Dict, Optional

import gspread
from oauth2client.service_account import ServiceAccountCredentials


class GoogleSheetDocument:
    """A Google Sheet with supreme-pancake configuration worksheets"""

    _client: gspread.client.Client
    """gspread Google client object"""
    _credential_path: str
    """Path of the credential file"""
    _sheet_key: str
    """Key of the google sheet

    See also:
        `How do I find my Google Sheet Key? <https://support.qooqee.com/hc/
        en-us/articles/360000471814-How-do-I-find-my-Google-Sheet-Key->`_
    """
    _sheet_sp_conf: Optional[gspread.models.Worksheet]
    """The 'sp_conf' worksheet model"""
    _sheet_sp_data: gspread.models.Worksheet
    """The 'sp_data' worksheet model"""
    _sheet_sp_queries: gspread.models.Worksheet
    """The 'sp_queries' worksheet model"""
    _spreadsheet: gspread.models.Spreadsheet
    """gspread spreadsheet object"""
    def __init__(self, credential_path: str, sheet_key: str):
        self._credential_path = credential_path
        self._sheet_key = sheet_key
        logging.info('Opening sheet "%s" with credentials "%s"', sheet_key,
                     credential_path)
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            credential_path, ['https://spreadsheets.google.com/feeds'])
        self._client = gspread.authorize(credentials)
        self._spreadsheet = self._client.open_by_key(sheet_key)
        worksheets = [ws.title for ws in self._spreadsheet.worksheets()]
        logging.debug("Available worksheets %s", str(worksheets))
        if 'sp_conf' in worksheets:
            self._sheet_sp_conf = self._spreadsheet.worksheet('sp_conf')
        else:
            self._sheet_sp_conf = None
        if 'sp_data' in worksheets:
            self._sheet_sp_data = self._spreadsheet.worksheet('sp_data')
        else:
            logging.error('Worksheet "sp_data" not found')
            raise ValueError('Worksheet "sp_data" not found')
        if 'sp_queries' in worksheets:
            self._sheet_sp_queries = self._spreadsheet.worksheet('sp_queries')
        else:
            logging.error('Worksheet "sp_queries" not found')
            raise ValueError('Worksheet "sp_queries" not found')
