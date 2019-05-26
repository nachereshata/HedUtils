import platform
import re
import sys
from collections import namedtuple
from pathlib import Path
from typing import List

import psutil

from hed_utils.support import log
from hed_utils.support.persistence import file_sys

__author__ = "nachereshata"
__copyright__ = "nachereshata"
__license__ = "mit"

KillVictim = namedtuple("KillVictim", "ppid pid name status")

IS_WINDOWS = platform.system() == "Windows"

IS_LINUX = platform.system() == "Linux"

IS_MAC = platform.system() in ("Darwin", "macosx")

IS_64BITS = sys.maxsize > 2 ** 32


@log.call
def _kill(process: psutil.Process, timeout=5) -> bool:
    """Attempts to kill the process in a fail-safe manner and returns status

    Tries to terminate the process first and waits for it for the given timeout.
    If termination fails - attempts to kill the process instead and wait for it to die.

    Args:
        process(Process):   the process that is to be killed
        timeout(int):       the timeout to wait after each terminate/kill attempt

    Returns:
        obj(bool):          True if the process has been killed/terminated,
                            False if the process is still running after this method returns
    """

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
def _rkill(process: psutil.Process, *, dry=True) -> List[KillVictim]:
    victims = []

    if process.is_running():

        with process.oneshot():

            ppid = process.ppid()
            pid = process.pid
            name = process.name()

        for child_process in process.children(recursive=True):
            victims.extend(_rkill(child_process, dry=dry))

        victims.append(KillVictim(ppid, pid, name, ("SKIPPED" if dry else _kill(process))))

    return victims


@log.call
def kill_process_by_name(name: str, *, ignorecase=False, dry=True) -> List[KillVictim]:
    if not name:
        raise ValueError(f"name not set!({name})")

    if not isinstance(name, str):
        raise TypeError(f"name must be str! ({name})")

    victims = []
    target_name = name.lower() if ignorecase else name

    for process in psutil.process_iter():
        process_name = process.name().lower() if ignorecase else process.name()

        if process_name == target_name:
            victims.extend(_rkill(process, dry=dry))

    return victims


@log.call
def kill_process_by_pid(pid, dry=True) -> List[KillVictim]:
    if not pid:
        raise ValueError(f"pid not set! ({pid})")
    return _rkill(psutil.Process(pid=int(pid)), dry=dry)


@log.call
def kill_process_by_pattern(pattern: str, ignorecase=False, dry=True) -> List[KillVictim]:
    if not pattern:
        raise ValueError(f"pattern not set!({pattern})")
    if not isinstance(pattern, str):
        raise TypeError(f"pattern must be str! ({type(pattern).__name__}) {pattern}")

    victims = []

    for process in psutil.process_iter():
        process_name = process.name()

        if ignorecase:
            should_kill = bool(re.findall(pattern, process_name, flags=re.IGNORECASE))
        else:
            should_kill = bool(re.findall(pattern, process_name))

        if should_kill:
            victims.extend(_rkill(process, dry=dry))

    return victims


@log.call(log_result=False)
def kill_all(*, name=None, pattern=None, pid=None, ignorecase=False, dry=False) -> List[KillVictim]:
    victims = []

    if name is not None:
        victims.extend(kill_process_by_name(name, ignorecase=ignorecase, dry=dry))

    if pattern is not None:
        victims.extend(kill_process_by_pattern(pattern, ignorecase=ignorecase, dry=dry))

    if pid is not None:
        victims.extend(kill_process_by_pid(pid, dry=dry))

    return victims


@log.call
def view_file(path, safe=False):
    from multiprocessing import Process
    from subprocess import call
    from functools import partial

    path = (path if isinstance(path, Path) else Path(path)).absolute()

    if not path.exists():
        raise FileNotFoundError(path)

    if safe:
        path = file_sys.copy_to_tmp(path)

    @log.call
    def get_view_cmd():

        if IS_WINDOWS:
            return ["cmd", "/c"]

        if IS_LINUX:
            return ["xdg-open"]

        raise OSError("Unsupported os")

    process = Process(target=partial(call, get_view_cmd() + [str(path)]))
    process.start()
    process.join(timeout=5)

    return path


@log.call(skip_args=["text"])
def view_text(text: str):
    file = file_sys.get_tmp_location("text_view.txt")
    file_sys.write_text(text=text, file=file)
    view_file(file, safe=True)
