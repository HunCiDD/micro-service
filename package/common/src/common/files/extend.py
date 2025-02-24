__all__ = [
    "JsonFile",
    "IniFile",
    "XmlFile",
    "YamlFile",
]

import json
from configparser import ConfigParser
from typing import Any, Callable, Dict, Optional

import yaml
from defusedxml import ElementTree

from .base import FileException, File
from ..data.encoder import JsonEncoder


class JsonFile(File):
    ALLOWED_SUFFIX = (".json",)

    def load(
        self, encoding: str = "utf-8", hook: Optional[Callable] = None
    ) -> Dict[str, Any]:
        data = {}
        with self.open("r", encoding=encoding) as fp:
            data.update(json.load(fp))

            if hook:
                data = hook(data)
        return data

    def dump(self, data: Dict[str, Any], encoding: str = "utf-8"):
        with self.open("w", encoding=encoding) as fp:
            json.dump(data, fp, indent=4, cls=JsonEncoder)


class IniFile(File):
    ALLOWED_SUFFIX = (".ini", ".conf", ".env")

    def load(
        self, encoding: str = "utf-8", hook: Optional[Callable] = None
    ) -> Dict[str, Any]:
        data = {}
        parser = ConfigParser()
        parser.read(self._path, encoding=encoding)
        for section in parser.sections():
            section_data = {}
            for key, value in parser.items(section):
                section_data[key] = value
            data[section] = section_data

        if hook:
            data = hook(data)
        return data

    def dump(self, data: Dict[str, Any], encoding: str = "utf-8"):
        raise FileException("Dump not support")


class XmlFile(File):
    ALLOWED_SUFFIX = (".xml",)

    def load(
        self, encoding: str = "utf-8", hook: Optional[Callable] = None
    ) -> Dict[str, Any]:
        _parser = ElementTree.XMLParser(
            encoding=encoding, forbid_dtd=True, forbid_entities=True
        )
        data = {}
        with self.open("r", encoding=encoding) as fp:
            tree = ElementTree.parse(fp, parser=_parser)
            if hook:
                data = hook(data, tree)
        return data


class YamlFile(File):
    ALLOWED_SUFFIX = (".yaml",)

    def load(
        self, encoding: str = "utf-8", hook: Optional[Callable] = None
    ) -> Dict[str, Any]:
        data = {}
        with self.open("r", encoding=encoding) as fp:
            data.update(yaml.safe_load(fp))

            if hook:
                data = hook(data)
        return data
