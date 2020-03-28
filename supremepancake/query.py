"""Query module"""

import datetime

from typing import Any, Callable, cast, List, Optional

from jsonpath_ng import parse
import requests

UNKNOWN_ERROR = -999
INVALID_QUERY = -100
INVALID_OR_UNSUPPORTED_HTTP_METHOD = -101
INVALID_URL = -102
JSONPATH_ERROR = -110
JSONPATH_SYNTAX_ERROR = -111
AGGREGATION_ERROR = -120
AGGREGATION_INVALID_OPERATOR = -121
AGGREGATION_WRONG_DATATYPE = -122
AGGREGATION_ARITHMETIC_ERROR = -123
NO_ERROR = 0


class QueryError(Exception):
    """An exception describing a query error"""
    def __init__(self, code: int, message: str):
        super().__init__(self, message)
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f'({self.code}) {self.message}'


class Query:
    """Represents a query according to the v1 specification

    The execution of a query is decomposed in 3 steps:
    1. a REST API call;
    2. pass the returned JSON document through a JSONPath query;
    3. apply an optional aggregation operator.
    """

    _aggregation: str
    """The aggregation operator (see specification)"""
    _http_method: str
    """HTTP method for REST API call"""
    _jsonpath_query: str
    """The JSONPath query

    See also:
        `JSONPath Reference <https://goessner.net/articles/JsonPath/>`
    """
    _url: str
    """URL for REST API call"""
    _valid: bool
    """Wether the query is valid"""
    def __init__(self, parameter_list: List[str]):
        if len(parameter_list) == 4:
            self._valid = True
            self._http_method = parameter_list[0]
            self._url = parameter_list[1]
            self._jsonpath_query = parameter_list[2]
            self._aggregation = parameter_list[3]
        else:
            self._valid = False

    def _execute_aggregation(self, data: Any) -> Any:
        """Applies an aggregation operator"""
        if self._aggregation == '':
            return data
        if self._aggregation == 'AVG':
            raise NotImplementedError
        if self._aggregation == 'COUNT':
            assert_isinstance(data, List)
            return len(data)
        if self._aggregation == 'MAX':
            raise NotImplementedError
        if self._aggregation == 'MED':
            raise NotImplementedError
        if self._aggregation == 'MIN':
            raise NotImplementedError
        if self._aggregation == 'STDEV':
            raise NotImplementedError
        if self._aggregation == 'SUM':
            raise NotImplementedError
        if self._aggregation == 'VAR':
            raise NotImplementedError
        raise QueryError(AGGREGATION_INVALID_OPERATOR,
                         f'Unknown aggregation operator {self._aggregation}')

    def _execute_jsonpath(self, data: Any) -> List[Any]:
        """Applies a JSONPath filter on a data in string form"""
        if self._jsonpath_query == '':
            return data
        try:
            jsonpath_expr = parse(self._jsonpath_query)
            return [match.value for match in jsonpath_expr.find(data)]
        except Exception as error:
            raise QueryError(JSONPATH_SYNTAX_ERROR, str(error))

    def _execute_rest(self) -> Any:
        """Runs the REST API call"""
        function = {
            # 'DELETE': requests.delete,
            'GET': requests.get,
            'POST': requests.post,
            # 'PUT': requests.put
        }.get(self._http_method.upper(), None)
        function = cast(Optional[Callable[..., requests.Response]], function)
        if not function:
            raise QueryError(
                INVALID_OR_UNSUPPORTED_HTTP_METHOD,
                f'Unknown or unsopported HTTP method {self._http_method}')
        headers = {
            'Accept-Encoding': 'gzip',
            'accept': 'application/json',
            'User-Agent': 'supreme-pancake'
        }
        response: requests.Response = function(self._url, headers=headers)
        if response.status_code >= 400:
            raise QueryError(response.status_code, response.reason)
        try:
            return response.json()
        except ValueError:
            raise QueryError(INVALID_QUERY, 'Could not parse response JSON')

    def execute(self) -> List[Any]:
        """Runs the query"""
        query_start = timestamp()
        try:
            stage1 = self._execute_rest()
            stage2 = self._execute_jsonpath(stage1)
            stage3 = self._execute_aggregation(stage2)
            size = len(str(stage3).encode('UTF-8'))
            length = len(stage3) if isinstance(stage3, List) else -1
            return [
                str(stage3), size, length, '0', '', query_start,
                timestamp()
            ]
        except QueryError as error:
            return [
                '', '0', '-1', error.code, error.message, query_start,
                timestamp()
            ]
        except Exception as error:  # pylint: disable=broad-except
            return [
                '', '0', '-1', UNKNOWN_ERROR,
                str(error), query_start,
                timestamp()
            ]


def assert_isinstance(obj: object, typ: type):
    """Asserts that an object has a certain type, otherwise raises a
    :class:`QueryError`"""
    if not isinstance(obj, typ):
        raise QueryError(AGGREGATION_WRONG_DATATYPE,
                         f'Type of data is {type(obj)}, excpected {str(typ)}')


def timestamp() -> str:
    """Returns a UTC timestamp"""
    return str(datetime.datetime.now(datetime.timezone.utc))
