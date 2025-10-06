import os
import pytest
from lus import LusFile

def test_run_cd(tmp_path):
    lusfile = LusFile("")
    with pytest.raises(FileNotFoundError):
        lusfile.run(["cd", "non_existent_directory"], {})
    test_dir = tmp_path / "subdir"
    test_dir.mkdir()
    cwd = os.getcwd()
    assert cwd != str(test_dir)
    lusfile = LusFile("")
    lusfile.run(["cd", str(test_dir)], {})
    assert os.getcwd() == str(test_dir)
    lusfile.run(["cd", "-"], {})
    assert os.getcwd() == cwd
