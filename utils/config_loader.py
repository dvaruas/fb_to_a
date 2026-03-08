import inspect
import json
from typing import Type, TypeVar

T = TypeVar("T")


def load_config_from_json(cls: Type[T], file_path: str) -> T:
    with open(file_path, "r") as fr:
        data = json.load(fr)
    params = inspect.signature(cls).parameters
    filtered = {k: v for k, v in data.items() if k in params}
    return cls(**filtered)
