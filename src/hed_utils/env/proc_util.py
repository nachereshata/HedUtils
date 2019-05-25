import re

import psutil

from hed_utils import log

__author__ = "nachereshata"
__copyright__ = "nachereshata"
__license__ = "mit"


def processes_with_name(name):
    for process in psutil.process_iter():
        if process.name() == name:
            yield process


def processes_with_name_matching(pattern):
    for process in psutil.process_iter():
        if re.findall(pattern, process.name()):
            yield process


@log.call
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


@log.call(skip_args=["victims"], log_result=False)
def rkill(process: psutil.Process, victims=None, dry=False):
    """Attempts to recursively kill a process, by killing itś children first."""

    if victims is None:
        victims = []

    if process.is_running():

        with process.oneshot():
            victim = dict(ppid=process.ppid(), pid=process.pid, name=process.name())

            for child in process.children(recursive=True):
                rkill(child, victims, dry)

        victim["success"] = "SKIPPED" if dry else kill(process)

        victims.append(victim)

    return victims


@log.call(log_result=False)
def kill_all(*, name=None, pattern=None, dry=False):
    victims = []

    if name is not None:
        for target in processes_with_name(name):
            rkill(process=target, victims=victims, dry=dry)

    if pattern is not None:
        for target in processes_with_name_matching(pattern):
            rkill(target, victims, dry)

    if victims:
        victims.sort(key=(lambda v: v["ppid"]))

    return victims
