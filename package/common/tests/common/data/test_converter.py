import pytest

from common.data.converter import FloatConverter


def test_to_int_success(self):
    assert FloatConverter.to_int(123.45) == 123


if __name__ == '__main__':
    pytest.main()
