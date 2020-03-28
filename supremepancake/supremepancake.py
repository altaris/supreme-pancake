"""Main module, containing the entry point"""

import argparse
import logging

# pylint: disable=no-name-in-module
from __init__ import __version__

from googlesheetdocument import GoogleSheetDocument


def init_logging(logging_level_str: str) -> None:
    """Inits the logging facility.

    See also:
        `logging documentation
        <https://docs.python.org/3.8/library/logging.html>`_
    """
    logging_level = {
        'CRITICAL': logging.CRITICAL,
        'DEBUG': logging.DEBUG,
        'ERROR': logging.ERROR,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING
    }.get(logging_level_str.upper(), logging.WARNING)
    logging.basicConfig(format='%(asctime)s [%(levelname)-7s] %(message)s',
                        level=logging_level)


def main() -> None:
    """Main function."""
    args = parse_command_line_arguments()
    init_logging(args.logging_level)
    logging.info('Starting supreme-pancake v%s', __version__)
    logging.debug('Command line arguments %s', str(args))
    document = GoogleSheetDocument(args.credentials, args.sheet_key)
    document.execute_all_queries()


def parse_command_line_arguments() -> argparse.Namespace:
    """Specifies the command line parser and returns a
    :class:`argparse.Namespace` containing the arguments."""
    parser = argparse.ArgumentParser(
        description=f'supreme-pancake v{__version__}')
    parser.add_argument('-c',
                        '--credentials',
                        action='store',
                        help='Credential JSON file')
    parser.add_argument(
        '-l',
        '--logging-level',
        action='store',
        default='INFO',
        help='Logging level, either "DEBUG", "INFO", "WARNING", "ERROR", '
        'or "CRITICAL"')
    parser.add_argument('-s',
                        '--sheet-key',
                        action='store',
                        help='Google Sheet key')
    return parser.parse_args()


if __name__ == '__main__':
    main()
