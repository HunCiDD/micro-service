# 数据生成器
__all__ = [
    "RandomStringGenerator",
    "RandomFloatGenerator",
    "RandomIntGenerator",
    "UuidGenerator",
]

import secrets
import string
import time
from uuid import NAMESPACE_DNS, UUID, uuid5


class RandomIntGenerator:
    @staticmethod
    def by_range(start: int = 0, end: int = 10) -> int:
        secrets_generator = secrets.SystemRandom()
        return secrets_generator.randint(start, end)


class RandomStringGenerator:
    @staticmethod
    def by_length(length: int = 10) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))


class RandomFloatGenerator:
    # Generate random floating-point numbers

    @staticmethod
    def by_range(start: float = 0.0, end: float = 1.0) -> float:
        secrets_generator = secrets.SystemRandom()
        return secrets_generator.uniform(start, end)


class UuidGenerator:
    @staticmethod
    def by_value(value: str, random: bool = False) -> UUID:
        random_num = RandomIntGenerator.by_range(0, 10000) if random else 0
        return uuid5(NAMESPACE_DNS, f"{value}{random_num}")

    @staticmethod
    def by_time(random: bool = False) -> UUID:
        random_num = RandomIntGenerator.by_range(0, 10000) if random else 0
        return uuid5(NAMESPACE_DNS, f"{time.time()}{random_num}")
