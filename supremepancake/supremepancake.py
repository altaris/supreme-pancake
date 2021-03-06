"""Main module, containing the entry point"""

import argparse
import logging
from typing import Dict, List

# pylint: disable=no-name-in-module
from __init__ import __version__

from googlesheet import GoogleSheet


def init_logging(logging_level_str: str) -> None:
    """Inits the logging facility.

    See also:
        `logging documentation
        <https://docs.python.org/3.8/library/logging.html>`_
    """
    logging_level = {
        "CRITICAL": logging.CRITICAL,
        "DEBUG": logging.DEBUG,
        "ERROR": logging.ERROR,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
    }.get(logging_level_str.upper(), logging.WARNING)
    logging.basicConfig(
        format="%(asctime)s [%(levelname)-8s] %(message)s",
        level=logging_level,
    )


def main() -> None:
    """Main function."""
    args = parse_command_line_arguments()
    init_logging(args.logging_level)
    logging.info("Starting supreme-pancake v%s", __version__)
    logging.debug("Command line arguments %s", str(args))
    if args.one_shot:
        document = GoogleSheet(
            args.credentials,
            args.sheet_key,
            parse_secrets(args.secret),
        )
        document.execute_all_queries()
    else:
        raise NotImplementedError


def parse_command_line_arguments() -> argparse.Namespace:
    """Specifies the command line parser and returns a
    :class:`argparse.Namespace` containing the arguments."""
    parser = argparse.ArgumentParser(
        description=f"supreme-pancake v{__version__}")
    parser.add_argument(
        "-c",
        "--credentials",
        action="store",
        help="Credential JSON file",
    )
    parser.add_argument(
        "-k",
        "--sheet-key",
        action="store",
        help="Google Sheet key",
    )
    parser.add_argument(
        "-l",
        "--logging-level",
        action="store",
        default="INFO",
        help='Logging level, either "DEBUG", "INFO", "WARNING", "ERROR", '
        'or "CRITICAL"',
    )
    parser.add_argument(
        "--one-shot",
        action="store_true",
        default=False,
        help="Runs all queries once and exit",
    )
    parser.add_argument(
        "-s",
        "--secret",
        action="append",
        default=[],
        help='Adds a secret. Example: "-s PASS=123456789". Can be used '
        'multiple times',
    )
    return parser.parse_args()


def parse_secrets(raw: List[str]) -> Dict[str, str]:
    """Parses secrets"""
    result: Dict[str, str] = {}
    for raw_secret in raw:
        keyval = raw_secret.split('=', 1)
        if len(keyval) != 2:
            raise ValueError(f'Invalid secret "{raw_secret}"')
        result[keyval[0]] = keyval[1]
    return result


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # pylint: disable=broad-except
        logging.critical("%s: %s", type(error).__name__, str(error))
