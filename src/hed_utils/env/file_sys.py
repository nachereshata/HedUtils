from datetime import datetime
from functools import partial
from multiprocessing import Process
from pathlib import Path
from platform import system
from shutil import copyfile, copytree
from subprocess import call
from tempfile import gettempdir
from typing import Union

from hed_utils import log


@log.call
def get_utc_timestamp() -> str:
    return datetime.utcnow().strftime('%Y-%m-%d_%H_%M_%S_%f')


@log.call
def get_tmp_location(path) -> str:
    path = path if isinstance(path, Path) else Path(path)
    tmp_name = path.stem + "_tmp_" + get_utc_timestamp() + path.suffix
    return str(Path(gettempdir()).joinpath(tmp_name))


@log.call
def copy(src_path: str, dst_path: str, overwrite=False) -> str:
    src_path, dst_path = Path(src_path), Path(dst_path)

    if not src_path.exists():
        raise FileNotFoundError(src_path)

    if dst_path.exists():  # pragma: no cover
        if overwrite:
            delete(dst_path)
        else:
            raise FileExistsError(str(dst_path))

    copy_func = log.call(copyfile if src_path.is_file() else copytree)
    copy_path = copy_func(str(src_path), str(dst_path))
    return copy_path


@log.call
def copy_to_tmp(src_path) -> str:
    dst = get_tmp_location(src_path)
    return copy(str(src_path), str(dst), overwrite=True)


@log.call
def delete(path: Union[str, Path]):
    path = path if isinstance(path, Path) else Path(path)

    if not path.exists():
        raise FileNotFoundError(str(path))

    if path.is_file():
        path.unlink()
        return

    if path.is_dir():
        for child_path in path.iterdir():
            delete(child_path)

        path.rmdir()


@log.call
def is_windows() -> bool:
    return system() == "Windows"


@log.call
def is_linux() -> bool:
    return system() == "Linux"


@log.call
def is_file(path) -> bool:
    path = Path(path)
    return path.is_file() if path.exists() else bool(path.suffix)


@log.call
def view_file(path, safe=False):
    path = path if isinstance(path, Path) else Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    if safe:
        path = copy_to_tmp(path)

    @log.call
    def get_view_cmd():
        if is_windows():
            return ["cmd", "/c"]
        if is_linux():
            return ["xdg-open"]
        raise OSError("Unsupported os")

    process = Process(target=partial(call, get_view_cmd() + [str(path)]), daemon=True)
    process.start()
    process.join(timeout=5)
    return path


@log.call(skip_args=["text"])
def write_text(*, text: str, file: str):
    path = Path(file)
    with path.open("wb") as out:
        return out.write(text.encode("utf-8"))


@log.call(skip_args=["text"])
def view_text(text: str):
    file = get_tmp_location("text_view.txt")
    write_text(text=text, file=file)
    view_file(file, safe=True)
