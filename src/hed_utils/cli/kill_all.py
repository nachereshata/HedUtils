import argparse
import logging
import sys

from tabulate import tabulate

from hed_utils.support import log, os_util

__author__ = "nachereshata"
__copyright__ = "nachereshata"
__license__ = "mit"

_logger = logging.getLogger(__name__)


def _parse_args(args):
    parser = argparse.ArgumentParser("Kill processes by exact name or regex")

    parser.add_argument("-n", "--name",
                        dest="name",
                        help="Name of the processes to kill",
                        metavar="NAME",
                        type=str,
                        default=None)

    parser.add_argument("-p", "--pattern",
                        dest="pattern",
                        help="Regex pattern used for matching the process name",
                        metavar="PATTERN",
                        type=str,
                        default=None)

    parser.add_argument("-i", "--ignorecase",
                        dest="ignorecase",
                        help="Flag for matching the name/pattern",
                        action="store_const",
                        const=True,
                        default=False)

    parser.add_argument("-pid", "--pid",
                        dest="pid",
                        help="Process id of the target",
                        metavar="PID",
                        type=int,
                        default=None)

    parser.add_argument("-d", "--dry",
                        dest="dry",
                        help="Make a dry run (don't kill - just print the victims)",
                        action="store_const",
                        const=True,
                        default=True)

    parser.add_argument("-nd", "--not-dry",
                        dest="dry",
                        help="Not a dry run (kill and print the victims)",
                        action="store_const",
                        const=False,
                        default=True)

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
    print(f"kill_all(name='{args.name}', pattern='{args.pattern}', pid='{args.pid}', ignorecase='{args.ignorecase}', "
          f"dry='{args.dry}')")

    if args.loglevel:
        log.init(level=args.loglevel)

    victims = [victim._asdict()
               for victim
               in os_util.kill_all(name=args.name, pattern=args.pattern, pid=args.pid, dry=args.dry)]

    print(f"kill_all victims:\n" + tabulate(victims, headers="keys"))


def run():
    """Entry point for console_scripts"""

    main(sys.argv[1:])


if __name__ == "__main__":
    run()
