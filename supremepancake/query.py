"""Query module"""

import datetime
from decimal import Decimal
import json
import statistics

from typing import Any, Callable, cast, Dict, List, Optional

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
        return f"({self.code}) {self.message}"


# pylint: disable=too-few-public-methods
class Query:
    """Represents a query according to the v1 specification

    The execution of a query is decomposed in 3 steps:
    1. a REST API call;
    2. pass the returned JSON document through a JSONPath query;
    3. apply an optional aggregation operator.
    """

    _aggregation: str
    """The aggregation operator (see specification)"""
    _http_parameters: Dict[str, Any]
    """HTTP parameters"""
    _jsonpath_query: str
    """The JSONPath query

    See also:
        `JSONPath Reference <https://goessner.net/articles/JsonPath/>`
    """
    _secrets: Dict[str, str]
    """Secret dict, see ``-s`` command line option"""
    _valid: bool
    """Wether the query is valid"""

    def __init__(self, parameter_list: List[str], secrets: Dict[str, str]):
        try:
            self._http_parameters = json.loads(parameter_list[0])
            if 'request' not in self._http_parameters:
                raise ValueError
            if 'data' not in self._http_parameters['request']:
                self._http_parameters['request']['data'] = {}
            if 'headers' not in self._http_parameters['request']:
                self._http_parameters['request']['headers'] = {}
            if 'method' not in self._http_parameters['request']:
                raise ValueError
            if 'parameters' not in self._http_parameters['request']:
                self._http_parameters['request']['parameters'] = {}
            if 'url' not in self._http_parameters['request']:
                raise ValueError
            if 'response' not in self._http_parameters:
                self._http_parameters['response'] = {}
            if 'data' not in self._http_parameters['response']:
                self._http_parameters['response']['data'] = None
            if 'next' not in self._http_parameters['response']:
                self._http_parameters['response']['next'] = None
            self._jsonpath_query = parameter_list[1]
            self._aggregation = parameter_list[2]
            self._secrets = secrets
        except Exception:  # pylint: disable=broad-except
            self._valid = False
        else:
            self._valid = True

    def _execute_aggregation(self, data: Any) -> Any:
        """Applies an aggregation operator"""
        if self._aggregation == "":
            return data
        if self._aggregation == "COUNT":
            assert_isinstance(data, List)
            return len(data)
        if self._aggregation in [
                "AVG", "MAX", "MED", "MIN", "STDEV", "SUM", "VAR"
        ]:
            assert_isinstance(data, List)
            data = [Decimal(x) for x in data]
            function = {
                "AVG": statistics.mean,
                "MAX": max,
                "MED": statistics.median,
                "MIN": min,
                "STDEV": statistics.stdev,
                "SUM": sum,
                "VAR": statistics.variance,
            }[self._aggregation]
            function = cast(Callable, function)
            if not function:
                raise QueryError(
                    UNKNOWN_ERROR,
                    f"Failed to cast aggregation operator {self._aggregation}",
                )
            return function(data)
        raise QueryError(
            AGGREGATION_INVALID_OPERATOR,
            f"Unknown aggregation operator {self._aggregation}",
        )

    def _execute_jsonpath(self, data: Any) -> List[Any]:
        """Applies a JSONPath filter on a data in string form"""
        if self._jsonpath_query == "":
            return data
        try:
            jsonpath_expr = parse(self._jsonpath_query)
            return [match.value for match in jsonpath_expr.find(data)]
        except Exception as error:
            raise QueryError(JSONPATH_SYNTAX_ERROR, str(error))

    def _execute_rest(self) -> Any:
        """Runs the REST API call"""
        if self._http_parameters['response']['next']:
            next_page = self._http_parameters['request']['url']
            result: List = []
            while next_page:
                response_json = self._make_request(next_page)
                result.append(self._get_response_json_data(response_json))
                next_page = self._get_response_json_next_page(response_json)
            return result
        return self._make_request(self._http_parameters['request']['url'])

    def _get_response_json_data(self, response_json: Dict) -> Any:
        """Gets the data field from a response JSON document"""
        if self._http_parameters['response']['data'] is None:
            return response_json
        jsonpath_expr = parse(self._http_parameters['response']['data'])
        matches = [match.value for match in jsonpath_expr.find(response_json)]
        if matches:
            return matches[0]
        return None

    def _get_response_json_next_page(self,
                                     response_json: Dict) -> Optional[str]:
        """In case of paginated requests, gets the next page url, or None if
        there is no next page"""
        if self._http_parameters['response']['next'] is None:
            return None
        jsonpath_expr = parse(self._http_parameters['response']['next'])
        matches = [match.value for match in jsonpath_expr.find(response_json)]
        if matches:
            return matches[0]
        return None

    def _make_request(self, url: str) -> dict:
        """Executes a single HTTP request at a given url"""
        function = {
            "GET": requests.get,
            "POST": requests.post,
        }.get(self._http_parameters['request']['method'], None)
        function = cast(Optional[Callable[..., requests.Response]], function)
        if not function:
            raise QueryError(
                INVALID_OR_UNSUPPORTED_HTTP_METHOD,
                f"Unknown or unsopported HTTP method {self._http_parameters['request']['method']}",
            )
        try:
            response: requests.Response = function(
                url,
                headers=self._http_parameters['request']['headers'],
                data=self._http_parameters['request']['data'],
                params=self._http_parameters['request']['parameters'],
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError:
            raise QueryError(response.status_code, response.reason)
        except ValueError:
            raise QueryError(INVALID_QUERY, "Could not parse response JSON")

    def execute(self) -> List[Any]:
        """Runs the query"""
        query_start = timestamp()
        try:
            stage1 = self._execute_rest()
            stage2 = self._execute_jsonpath(stage1)
            stage3 = self._execute_aggregation(stage2)
            size = len(str(stage3).encode("UTF-8"))
            length = len(stage3) if isinstance(stage3, List) else -1
            return [
                str(stage3),
                size,
                length,
                '0',
                '',
                query_start,
                timestamp(),
            ]
        except QueryError as error:
            return [
                '',
                '0',
                '-1',
                error.code,
                error.message,
                query_start,
                timestamp(),
            ]
        except Exception as error:  # pylint: disable=broad-except
            return [
                '',
                '0',
                '-1',
                UNKNOWN_ERROR,
                str(type(error).__name__) + ': ' + str(error),
                query_start,
                timestamp(),
            ]


def assert_isinstance(obj: object, typ: type):
    """Asserts that an object has a certain type, otherwise raises a
    :class:`QueryError`"""
    if not isinstance(obj, typ):
        raise QueryError(
            AGGREGATION_WRONG_DATATYPE,
            f"Type of data is {type(obj)}, excpected {str(typ)}",
        )


def timestamp() -> str:
    """Returns a UTC timestamp"""
    return str(datetime.datetime.now(datetime.timezone.utc))
