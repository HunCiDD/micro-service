from pathlib import Path

import pytest

from common.files.extend import IniFile, JsonFile, YamlFile

CUR_DIR = Path(__file__).parent


@pytest.fixture
def get_test_file():
    return CUR_DIR / "files_tmp/test_file.txt"


@pytest.fixture
def temp_dir(tmp_path):
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()
    return dir_path


class TestJsonFile:
    def test_base(self):
        file_path = CUR_DIR / "files_tmp/test.json"

        jf = JsonFile(file_path)
        if jf.exist:
            jf.remove()

        data = {"key": "value"}
        jf.dump(data)
        assert jf.exist is True
        assert jf.suffix == ".json"

        loaded_data = jf.load()
        assert loaded_data == data

        jf.remove()


class TestIniFile:
    def test_base(self):
        file_path = CUR_DIR / "files_tmp/test.ini"
        ini_file = IniFile(file_path)

        loaded_data = ini_file.load()
        assert loaded_data["test"]["a"] == "1"


class TestYamlFile:
    def test_base(self):
        file_path = CUR_DIR / "files_tmp/test.yaml"
        yaml_file = YamlFile(file_path)

        loaded_data = yaml_file.load()
        assert loaded_data["test"]["a"] == 1


if __name__ == "__main__":
    pytest.main()
