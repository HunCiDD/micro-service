import os
from collections import UserDict
from pathlib import Path
from typing import Callable, List, Optional, Union

from .files.base import File


class ConfigsDict(UserDict):
    def _load(self): ...

    def reload(self):
        self._load()


class EnvConfigsDict(ConfigsDict):
    def __init__(self, keys: List[str], hook: Optional[Callable] = None):
        super().__init__()
        self._keys = [key.strip() for key in keys]
        self._hook = hook
        self._load()

    def _load(self):
        for key in self._keys:
            value = os.getenv(key, "").strip()
            self.data[key] = value

        if self._hook:
            self.data = self._hook(self.data)


class FileConfigsDict(ConfigsDict):
    def __init__(self, file: Union[str, Path, File], hook: Optional[Callable] = None):
        super().__init__()
        self._file = file if isinstance(file, File) else File(file)
        self._hook = hook
        self._load()

    def _load(self):
        self.data = self._file.load()
        if self._hook:
            self.data = self._hook(self.data)
