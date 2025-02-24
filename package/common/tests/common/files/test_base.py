from pathlib import Path

import pytest

from common.files.base import Dir, File

CUR_DIR = Path(__file__).parent


@pytest.fixture
def get_test_file():
    return CUR_DIR / "files_tmp/test_file.txt"


@pytest.fixture
def temp_dir(tmp_path):
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()
    return dir_path


class TestFile:
    def test_file_base(self):
        file_path = CUR_DIR / "files_tmp/test_file.txt"

        content = "test content"
        with open(file_path, "w", encoding="utf-8") as fp:
            fp.write(content)

        f = File(file_path)
        assert f.exist is True
        assert f.size == len(content)
        assert f.read() == content
        assert f.suffix == ".txt"
        assert f.name == "test_file.txt"

        f.write("new content")
        assert f.read() == "new content"


class TestDir:
    def test_dir_iters(self, temp_dir):
        _dir = Dir(temp_dir)
        items = _dir.iters()
        assert len(items) == 0


if __name__ == "__main__":
    pytest.main()
