import argparse
import logging
import sys

from tabulate import tabulate

from hed_utils import log

from hed_utils.env import proc_util

__author__ = "nachereshata"
__copyright__ = "nachereshata"
__license__ = "mit"

_logger = logging.getLogger(__name__)


def _parse_args(args):
    parser = argparse.ArgumentParser("Kill processes by exact name or regex")

    parser.add_argument("-n", "--name",
                        dest="name",
                        help="Exact name of the processes to kill",
                        metavar="NAME",
                        default=None)

    parser.add_argument("-p", "--pattern",
                        dest="pattern",
                        help="Regex pattern used for matching the process name",
                        metavar="PATTERN",
                        default=None)

    parser.add_argument("-d", "--dry",
                        dest="dry",
                        help="Make a dry run (don't kill - just log)",
                        action="store_const",
                        const=True,
                        default=False)

    parser.add_argument("-v", "--verbose",
                        dest="loglevel",
                        help="set loglevel to INFO",
                        action="store_const",
                        const=logging.INFO)

    parser.add_argument("-vv", "--very-verbose",
                        dest="loglevel",
                        help="set loglevel to DEBUG",
                        action="store_const",
                        const=logging.DEBUG)

    return parser.parse_args(args)


def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    args = _parse_args(args)

    if args.loglevel:
        log.init(args.loglevel)

    victims = proc_util.kill_all(name=args.name, pattern=args.pattern, dry=args.dry)
    _logger.debug(f"kill_all details:\n" + tabulate(victims, headers="keys"))


def run():
    """Entry point for console_scripts
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
