import inspect
import logging
import sys
from collections import OrderedDict
from datetime import datetime
from functools import wraps, partial
from pathlib import Path
from timeit import default_timer as now
from typing import Any, Dict, Optional, List

LOGGER_FMT = "%(levelname)-8s | %(name)-20s | %(indent)s %(message)s"
PREFIX_UTC = "%(utcnow)s | "

_logger = logging.getLogger("hed_utils")

debug = _logger.debug
info = _logger.info
warning = _logger.warning
exception = _logger.exception
error = _logger.error


class Indentation:
    def __init__(self, value="    ", size=0):
        self._value = value
        self._size = size

    def increment(self):
        self._size += 1

    def decrement(self):
        self._size -= 1

    def get(self) -> str:
        return self._size * self._value


_indentation = Indentation()


def add_tag_factory(tag, callback):
    old_factory = logging.getLogRecordFactory()

    def new_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.__dict__[tag] = callback()
        return record

    logging.setLogRecordFactory(new_factory)


def init(*, level=None, fmt=None, utc_prefix=True, file=None):
    if level is None:
        level = logging.DEBUG

    if fmt is None:
        fmt = LOGGER_FMT

    if utc_prefix:
        fmt = PREFIX_UTC + fmt

    logging.basicConfig(level=level, stream=sys.stdout, format=fmt)

    if "%(indent)" in fmt:
        add_tag_factory("indent", _indentation.get)

    if "%(utcnow)" in fmt:
        add_tag_factory("utcnow", lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f"))

    if file:
        formatter = logging.Formatter(fmt=fmt)
        handler = logging.FileHandler(filename=str(Path(file).absolute()), encoding="utf-8")
        handler.setFormatter(formatter)
        _logger.addHandler(handler)


class CallFormatter:

    def __init__(self, func):
        if not callable(func):
            raise TypeError(func)

        self.func = func
        self.func_module = getattr(func, "__module__", "unknown_module")
        self.func_name = getattr(func, "__name__", "unknown_method")
        self.func_signature = inspect.signature(func)
        self.func_args_key = self._get_args_key(self.func_signature)
        self.func_kwargs_key = self._get_kwargs_key(self.func_signature)
        self.func_default_args = self._get_default_args(self.func_signature, self.func_args_key, self.func_kwargs_key)

    @classmethod
    def _get_args_key(cls, signature: inspect.Signature) -> Optional[str]:
        for param_name, param in signature.parameters.items():
            if param.kind == param.VAR_POSITIONAL:
                return param_name
        return None

    @classmethod
    def _get_kwargs_key(cls, signature: inspect.Signature) -> Optional[str]:
        for param_name, param in signature.parameters.items():
            if param.kind == param.VAR_KEYWORD:
                return param_name
        return None

    @classmethod
    def _get_default_args(cls,
                          signature: inspect.Signature, args_key: str = None, kwargs_key: str = None) -> Dict[str, Any]:
        default_args = OrderedDict()
        for param_name, param in signature.parameters.items():
            default_value = param.default
            if default_value == inspect._empty:
                if param_name == args_key:
                    default_value = tuple()
                elif param_name == kwargs_key:
                    default_value = dict()
                else:
                    default_value = None
            default_args[param_name] = default_value
        return default_args

    @property
    def full_name(self) -> str:
        return f"{self.func_module}.{self.func_name}"

    def format_call(self, *args, skip_args: List[str] = None, **kwargs) -> str:
        skip_args = skip_args or []
        caller_args = self.func_signature.bind(*args, **kwargs).arguments
        effective_args = dict(self.func_default_args)
        effective_args.update(caller_args)
        result = f"{self.full_name}("

        for idx, (arg_name, arg_value) in enumerate(effective_args.items()):
            if arg_name == self.func_args_key:
                result += "*"
            if arg_name == self.func_kwargs_key:
                result += "**"
                arg_value = dict(arg_value)
                skip_keys = [key for key in arg_value.keys() if (key in skip_args)]
                for key in skip_keys:
                    tmp_value = arg_value[key]
                    arg_value[key] = f"<{type(tmp_value).__name__}, skipped"
                    if hasattr(tmp_value, "__len__"):
                        arg_value[key] += f", len:{len(tmp_value)}"
                    arg_value[key] += ">"

            result += f"{arg_name}=<{type(arg_value).__name__}"
            if arg_name not in skip_args:
                if isinstance(arg_value, str):
                    result += f", '{arg_value}'"
                else:
                    result += f", {arg_value}"
            else:
                result += ", skipped"
                if hasattr(arg_value, "__len__"):
                    result += f", len:{len(arg_value)}"
            result += ">"

            if idx < len(effective_args) - 1:
                result += ", "

        result += ")"
        return result


def call(func=None, *, level=logging.DEBUG, skip_args=None, log_result=True, name=None):
    if func is None:
        return partial(call, level=level, skip_args=skip_args, log_result=log_result, name=name)

    skip_args = skip_args or []

    if skip_args:
        for arg_name in skip_args:
            if not isinstance(arg_name, str):
                raise TypeError(f"skip_args must be list of strings! Was: {skip_args}")

    call_formatter = CallFormatter(func)
    call_logger = logging.getLogger(name if name else call_formatter.func_module)

    @wraps(func)
    def wrapper(*args, **kwargs):

        call_msg = "---> " + call_formatter.format_call(*args, skip_args=skip_args, **kwargs)
        call_logger.log(level, call_msg)
        _indentation.increment()

        start_time = now()
        try:
            call_result = func(*args, **kwargs)
            call_duration = now() - start_time
            call_result_type = type(call_result).__name__
            _indentation.decrement()

            if log_result:
                result_msg = f"<{call_result_type}, {call_result}>"
            else:
                result_msg = f"<{call_result_type}"
                if hasattr(call_result, "__len__"):
                    result_msg += f", len: {len(call_result)}"
                result_msg += f">"

            call_logger.log(level,
                            f"{call_formatter.full_name} <--- {result_msg} {call_duration * 1000:0.6f} ms.")
            return call_result

        except:
            call_duration = now() - start_time
            _indentation.decrement()
            call_logger.exception(
                f"{call_formatter.func_module}.{call_formatter.func_name} "
                f"<--- Exception after {call_duration * 1000:0.6f} ms.")
            raise

    return wrapper
