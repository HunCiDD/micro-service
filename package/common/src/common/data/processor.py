# 数据处理器

__all__ = [
    'StringProcessor',
    'ListProcessor',
    'DictProcessor',
]

from typing import List, Optional, Tuple


class StringProcessor:
    @staticmethod
    def replace_keys(data: str, keys: Optional[List[Tuple[str, str]]] = None) -> str:
        if not keys:
            return data
        for old_key, new_key in keys:
            data = data.replace(old_key, new_key)
        return data


class ListProcessor:
    @staticmethod
    def deduplicate(data: list) -> list:
        return list(set(data))

    @staticmethod
    def range(data: list, limit: int = 0, offset: int = -1) -> list:
        return data[limit:offset]


class DictProcessor:
    @staticmethod
    def rename_keys(data: dict, key_map: Optional[dict] = None) -> dict:
        if not key_map:
            return data

        new_dict = {}
        for key, value in data.items():
            if key in key_map:
                new_dict[key_map[key]] = value
            else:
                new_dict[key] = value
        return new_dict

    @staticmethod
    def filter_keys(data: dict, keys: Optional[list] = None) -> dict:
        if not keys:
            return data
        return {k: v for k, v in data.items() if k in keys}

    @staticmethod
    def delete_keys(data: dict, keys: Optional[list] = None) -> dict:
        if not keys:
            return data
        return {k: v for k, v in data.items() if k not in keys}
