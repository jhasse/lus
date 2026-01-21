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


@pytest.mark.skipif(os.name != "nt", reason="call command is Windows-only")
def test_run_call_batch_file(tmp_path):
    """Test that call command executes .bat files on Windows."""
    lusfile = LusFile("")
    cwd = os.getcwd()

    try:
        os.chdir(tmp_path)
        # Create a test batch file in a subdirectory
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        batch_file = scripts_dir / "test.bat"
        batch_file.write_text("@echo off\necho Hello from batch\nexit /b 0\n")

        # Should execute successfully using / in path
        lusfile.run(["call", "scripts/test.bat"], {})
    finally:
        os.chdir(cwd)


@pytest.mark.skipif(os.name != "nt", reason="call command is Windows-only")
def test_run_call_cmd_file(tmp_path):
    """Test that call command executes .cmd files on Windows."""
    lusfile = LusFile("")
    cwd = os.getcwd()

    try:
        os.chdir(tmp_path)
        # Create a test cmd file using / path
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        cmd_file = scripts_dir / "test.cmd"
        cmd_file.write_text("@echo off\necho Hello from cmd\nexit /b 0\n")

        # Should execute successfully using / in path
        lusfile.run(["call", "scripts/test.cmd"], {})
    finally:
        os.chdir(cwd)


@pytest.mark.skipif(os.name != "nt", reason="call command is Windows-only")
def test_run_call_missing_file(tmp_path):
    """Test that call command raises FileNotFoundError for missing files."""
    lusfile = LusFile("")
    cwd = os.getcwd()

    try:
        os.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            lusfile.run(["call", "scripts/nonexistent.bat"], {})
    finally:
        os.chdir(cwd)


@pytest.mark.skipif(os.name != "nt", reason="call command is Windows-only")
def test_run_call_wrong_extension(tmp_path):
    """Test that call command rejects non-batch files."""
    lusfile = LusFile("")
    cwd = os.getcwd()

    try:
        os.chdir(tmp_path)
        # Create a .txt file using / path
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        txt_file = scripts_dir / "test.txt"
        txt_file.write_text("not a batch file")

        with pytest.raises(ValueError, match="only supports .bat or .cmd files"):
            lusfile.run(["call", "scripts/test.txt"], {})
    finally:
        os.chdir(cwd)


@pytest.mark.skipif(os.name != "nt", reason="call command is Windows-only")
def test_run_call_no_arguments():
    """Test that call command requires a script argument."""
    lusfile = LusFile("")

    with pytest.raises(ValueError, match="requires a script file"):
        lusfile.run(["call"], {})


@pytest.mark.skipif(os.name != "nt", reason="call command is Windows-only")
def test_run_call_environment_variables(tmp_path):
    """Test that call command captures and persists environment variable changes."""
    lusfile = LusFile("")
    cwd = os.getcwd()

    try:
        os.chdir(tmp_path)
        # Create a batch file that sets environment variables
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        batch_file = scripts_dir / "setenv.bat"
        batch_file.write_text(
            "@echo off\n"
            "set MY_TEST_VAR=hello_world\n"
            "set ANOTHER_VAR=test123\n"
            "exit /b 0\n"
        )

        # Ensure these variables don't exist before
        if "MY_TEST_VAR" in os.environ:
            del os.environ["MY_TEST_VAR"]
        if "ANOTHER_VAR" in os.environ:
            del os.environ["ANOTHER_VAR"]

        # Run the batch file
        lusfile.run(["call", "scripts/setenv.bat"], {})

        # Verify the environment variables were set
        assert os.environ.get("MY_TEST_VAR") == "hello_world"
        assert os.environ.get("ANOTHER_VAR") == "test123"

        # Clean up
        if "MY_TEST_VAR" in os.environ:
            del os.environ["MY_TEST_VAR"]
        if "ANOTHER_VAR" in os.environ:
            del os.environ["ANOTHER_VAR"]
    finally:
        os.chdir(cwd)


@pytest.mark.skipif(os.name == "nt", reason="test non-Windows behavior")
def test_run_call_ignored_on_non_windows(tmp_path):
    """Test that call command is silently ignored on non-Windows platforms."""
    lusfile = LusFile("")
    cwd = os.getcwd()

    try:
        os.chdir(tmp_path)
        # Create a dummy file using / path (doesn't matter if it's valid)
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        batch_file = scripts_dir / "test.bat"
        batch_file.write_text("echo test")

        # Should return successfully without executing
        lusfile.run(["call", "scripts/test.bat"], {})
    finally:
        os.chdir(cwd)
