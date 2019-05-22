import re

import psutil

from hed_utils import log as _log

__author__ = "nachereshata"
__copyright__ = "nachereshata"
__license__ = "mit"


class iter_proc:
    @staticmethod
    def children(parent):
        ppid = parent.pid
        for child in psutil.process_iter():
            if ppid == child.ppid():
                yield child

    @staticmethod
    def with_name(name):
        for process in psutil.process_iter():
            if process.name() == name:
                yield process

    @staticmethod
    def with_name_matching(pattern):
        for process in psutil.process_iter():
            if re.findall(pattern, process.name()):
                yield process


def kill(process: psutil.Process, timeout=5) -> bool:
    """Attempts to kill the process in a fail-safe manner and returns status"""

    if not process.is_running():
        return True

    try:
        process.terminate()
        try:
            process.wait(timeout)
            return True
        except:
            process.kill()
            try:
                process.wait(timeout)
                return True
            except:
                pass
    except:
        pass

    return not process.is_running()


def rkill(process: psutil.Process, victims=None, dry=False):
    """Attempts to recursively kill a process, by killing itś children first."""

    if victims is None:
        victims = []

    if process.is_running():

        with process.oneshot():
            victim = dict(ppid=process.ppid(), pid=process.pid, name=process.name())

        for child in iter_proc.children(process):
            rkill(child, victims, dry)

        if dry:
            _log.info(f"skipping process: {victim}")
            victim["success"] = "SKIPPED"
        else:
            _log.info(f"killing process: {victim}")
            victim["success"] = kill(process)

        victims.append(victim)

    return victims


def kill_all(*, name=None, pattern=None, dry=False):
    _log.info(f"killing processes [name={name}, pattern={pattern}, dry={dry}]...")

    victims = []

    if name is not None:
        for target in iter_proc.with_name(name):
            rkill(target, victims, dry)

    if pattern is not None:
        for target in iter_proc.with_name_matching(pattern):
            rkill(target, victims, dry)

    if victims:
        victims.sort(key=(lambda v: v["ppid"]))

    _log.info(f"Count of victims: {len(victims)}")
    return victims


def open_file(file):
    psutil.Process