"""Query module"""

from typing import List


class Query:
    """Represents a query according to the v1 specification

    The execution of a query is decomposed in 3 steps:
    1. a REST API call;
    2. pass the returned JSON document through a JSONPath query;
    3. apply an optional aggregation operator.
    """

    def __init__(self, parameter_list: List[str]):
        pass