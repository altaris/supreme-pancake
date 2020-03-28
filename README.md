supreme-pancake
===============

(github found the name for this project)

[![Maintainability](https://api.codeclimate.com/v1/badges/d22d5a42582ad4f2d853/maintainability)](https://codeclimate.com/github/altaris/supreme-pancake/maintainability)
![Python 3](https://badgen.net/badge/Python/3/blue) [![MIT
License](https://badgen.net/badge/license/MIT/blue)](https://choosealicense.com/licenses/mit/)

Implements a `REST API -> JSONPath -> Google Sheet` dataflow. In more details:
1. performs REST `GET` calls that return JSON documents;
2. process them with [JSONPath
   queries](https://goessner.net/articles/JsonPath/);
3. inserts the result in a Google Sheet.

The parameters for point 1. and 2. are specified in the same Google Sheet
according to the structure specified below.

# Command line arguments

Run
```sh
supreme-pancake --help
```

# Sheet structure

## Version `1`

### Sheet structure

In every sheet, the first row is **always** ignored. Use it to label columns
and make the sheets more human-readable.

* `sp_conf` (read only, optional): This sheet works as a key-value store of
  options and configurations for `supreme-pancake`. Rows are expected to have
  the key name in column `A` and value in column `B`.
  * `interval` (default: `60`): Time interval (in seconds) at which the
    `supreme-pancake` configuration and query data are refreshed, i.e. the
    interval at which `supreme-pancake` reads the relevant sheets, executes
    queries and updates data.
  * `jitter` (default: `5`): Global request jitter (in seconds). When requests
    are scheduled, a random jitter is added to avoid request bursts.
  * `version` (default: `1`): Version of the spreadsheet structure to use.
* `sp_data` (write only, must exist): This sheet is where `supreme-pancake`
  will store the result of each query. The result of queries specified in
  `sq_queries` will be stored in column `A` of the corresponding row (i.e. the
  result of a query specified at row 42 will writted in row 42).
  * Column `A`: The result of the query.
  * Column `B`: Size of the result (in bytes).
  * Column `C`: Length of the result if it is a table, otherwise `-1`.
  * Column `D`: Error code (see below).
  * Column `E`: Error message.
  * Column `F`: Time when the query started.
  * Column `G`: Time when the query finished.
* `sp_queries` (read only, mist exist): Sheet storing the queries.
  * Column `A`: HTTP method. Currently supported methods are `GET` and `POST`.
  * Column `B`: URL (with the `https://` and all).
  * Column `C`: JSONPath query.
  * Column `D`: Optional aggregation operator (see below).

### Aggregation operators

* `AVG` (expects a list of numbers): Average of the list.
* `COUNT` (expects a list): Length of the list.
* `MAX` (expects a list of numbers): Maximal element of the list.
* `MED` (expects a list of numbers): Median element of the list.
* `MIN` (expects a list of numbers): Minimal element of the list.
* `STDEV` (expects a list of numbers): Statistical standard deviation of the
  list.
* `SUM` (expects a list of numbers): Sum of all the elements of the list.
* `VAR` (expects a list of numbers): Statistical variance of the list.

### Error codes

* `-1xx`: Invalid query.
  * `-100`: Generic query error, refer to error message.
  * `-101`: Invalid or unsupported HTTP method.
  * `-102`: Invalid URL.
  * `-110`: Generic JSONPath error.
  * `-111`: Invalid JSONPath query (syntax error).
  * `-120`: Generic aggregation error
  * `-121`: Invalid aggregation operator.
  * `-121`: Invalid datatype for specified aggregation operator (e.g. `AVG` not
    receiving a table if numbers).
  * `-122`: Arithmetic error during aggregation.
* `0`: No error :ok_hand:.
* `4xx`: [HTTP client error
  code](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#4xx_Client_errors).
* `5xx`: [HTTP server error
  code](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#5xx_Server_errors).


# Development

## Dependencies

* `python3.8`
* `requirements.txt` for runtime dependencies
* `requirements.dev.txt` for development dependencies

Simply run
```sh
virtualenv venv -p python3.8
pip install -r requirements.txt
pip install -r requirements.dev.txt
```

## Running

```sh
make run  # Default command line arguments are '--help'
RUN_ARGS='--verbose' make run  # Custom command line arguments
```

## Documentation

Simply run
```sh
make docs
```
This will generate the HTML doc of the project, and the index file should be at
`out/docs/html/index.html`.

## Code quality

Don't forget to run
```sh
make
```
to format the code following [pep8](https://www.python.org/dev/peps/pep-0008/),
typecheck it using [mypy](http://mypy-lang.org/), and lint check it. Note that
the formatter [yapf](https://github.com/google/yapf) does not yet support
Python 3.8 (see [issue #772](https://github.com/google/yapf/issues/772)), so
please refrain from using the walrus operator.

# References

* [Google Sheet API for
  Python](https://developers.google.com/sheets/api/quickstart/python);
* [jsonpath-ng](https://github.com/h2non/jsonpath-ng), [Additional reference
  about JSONPath](https://goessner.net/articles/JsonPath/)
