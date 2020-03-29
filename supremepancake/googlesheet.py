"""Google Sheet module

See also:
    `gspread homepage <https://github.com/burnash/gspread>`_
    `gspread documentation <https://gspread.readthedocs.io/en/latest/>`_
"""

import logging
from typing import Any, Dict, List, Optional

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from query import Query


class GoogleSheet:
    """A Google Sheet with supreme-pancake configuration worksheets"""

    _client: gspread.client.Client
    """gspread Google client object"""
    _secrets: Dict[str, str]
    """Secret dict, see ``-s`` command line option"""
    _sheet_sp_conf: Optional[gspread.models.Worksheet]
    """The 'sp_conf' worksheet model"""
    _sheet_sp_data: gspread.models.Worksheet
    """The 'sp_data' worksheet model"""
    _sheet_sp_queries: gspread.models.Worksheet
    """The 'sp_queries' worksheet model"""
    _spreadsheet: gspread.models.Spreadsheet
    """gspread spreadsheet object"""

    def __init__(self, credential_path: str, sheet_key: str,
                 secrets: Dict[str, str]):
        logging.info('Opening sheet "%s" with credentials "%s"', sheet_key,
                     credential_path)
        self._authorize_client(credential_path)
        self._open_spreadsheet(sheet_key)
        self._secrets = secrets

    def _authorize_client(self, credential_path: str) -> None:
        """Authorizes a Google Sheet client"""
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            credential_path, ["https://spreadsheets.google.com/feeds"])
        self._client = gspread.authorize(credentials)

    def _open_spreadsheet(self, sheet_key: str) -> None:
        """Opens a spreadsheet"""
        self._spreadsheet = self._client.open_by_key(sheet_key)
        try:
            self._sheet_sp_conf = self._spreadsheet.worksheet("sp_conf")
        except gspread.exceptions.WorksheetNotFound:
            self._sheet_sp_conf = None
        try:
            self._sheet_sp_data = self._spreadsheet.worksheet("sp_data")
            self._sheet_sp_queries = self._spreadsheet.worksheet("sp_queries")
        except gspread.exceptions.WorksheetNotFound as error:
            raise ValueError(f'Worksheet "{str(error)}" not found')

    def execute_all_queries(self):
        """Executes all the queries specified in worksheet 'sp_queries'"""
        results: List[List] = [query.execute() for query in self.get_queries()]
        self._sheet_sp_data.clear()
        self._sheet_sp_data.update(
            f"A1:G1",
            [[
                "result",
                "size",
                "length",
                "error_code",
                "error_message",
                "query_start",
                "query_end",
            ]],
        )
        self._sheet_sp_data.update(f"A2:G{len(results) + 1}", results)

    def get_config(self) -> Dict[str, str]:
        """Returns a dict of configurations options as specified in worksheet 'sp_config'"""
        config: Dict[str, Any] = {
            "interval": 60,
            "jitter": 5,
            "version": 1,
        }
        if self._sheet_sp_conf:
            for row in self._sheet_sp_conf.get_all_values()[1:]:
                config[row[0]] = row[1]
        return config

    def get_queries(self) -> List[Query]:
        """Returns a list of queries specified by worksheet 'sp_queries'"""
        return [
            Query(row, self._secrets)
            for row in self._sheet_sp_queries.get_all_values()[1:]
        ]
