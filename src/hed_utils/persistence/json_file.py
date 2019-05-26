from json import dumps, loads
from pathlib import Path

from hed_utils.support import log


@log.call
def read_json(file: str):
    path = Path(file).absolute()
    log.debug(f"reading json file: {str(path)}")
    with path.open("rb") as in_file:
        return loads(in_file.read().decode(encoding="utf-8"))


@log.call
def write_json(obj, file: str):
    path = Path(file).absolute()
    log.debug(f"writing ({type(obj).__name__}) to json file: {str(path)}")
    with path.open("wb") as out_file:
        out_file.write(dumps(obj).encode(encoding="utf-8"))
