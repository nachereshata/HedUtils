import logging
import sys
from hed_utils.timestamp import utcnow

LOGGER_FMT = "| %(cpu)s | %(utcnow)s | %(levelname)-8s | %(module)-10s | L:%(lineno)-4s | %(funcName)-10s | %(message)s"

debug = logging.debug
info = logging.info
warning = logging.warning
exception = logging.exception
error = logging.error


def add_tag_factory(tag, callback):
    old_factory = logging.getLogRecordFactory()

    def new_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        print(record)
        record.__dict__[tag] = callback()
        return record

    logging.setLogRecordFactory(new_factory)


def init(loglevel=None, logformat=None):
    if loglevel is None:
        loglevel = logging.DEBUG

    if logformat is None:
        logformat = LOGGER_FMT

    logging.basicConfig(level=loglevel, stream=sys.stdout, format=logformat)

    if "%(utcnow)s" in logformat:
        add_tag_factory("utcnow", utcnow)

    if "%(cpu)s" in logformat:
        from functools import partial
        import psutil
        cpu_getter = partial(psutil.cpu_percent,percpu=True)
        add_tag_factory("cpu", cpu_getter)

def main():
    info("asdas")

if __name__ == '__main__':
    init()
    main()
