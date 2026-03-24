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


@pytest.mark.skipif(os.name == "nt", reason="source command is Unix-only")
def test_run_source_shell_script(tmp_path):
    """Test that source command executes shell scripts."""
    lusfile = LusFile("")
    cwd = os.getcwd()

    try:
        os.chdir(tmp_path)
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        script = scripts_dir / "setup.sh"
        script.write_text("export LUS_TEST_SOURCE=hello\n")

        if "LUS_TEST_SOURCE" in os.environ:
            del os.environ["LUS_TEST_SOURCE"]

        lusfile.run(["source", "scripts/setup.sh"], {})

        assert os.environ.get("LUS_TEST_SOURCE") == "hello"

        del os.environ["LUS_TEST_SOURCE"]
    finally:
        os.chdir(cwd)


@pytest.mark.skipif(os.name == "nt", reason="source command is Unix-only")
def test_run_source_dot_syntax(tmp_path):
    """Test that . (dot) syntax works as an alias for source."""
    lusfile = LusFile("")
    cwd = os.getcwd()

    try:
        os.chdir(tmp_path)
        script = tmp_path / "env.sh"
        script.write_text("export LUS_DOT_TEST=works\n")

        if "LUS_DOT_TEST" in os.environ:
            del os.environ["LUS_DOT_TEST"]

        lusfile.run([".", str(script)], {})

        assert os.environ.get("LUS_DOT_TEST") == "works"

        del os.environ["LUS_DOT_TEST"]
    finally:
        os.chdir(cwd)


@pytest.mark.skipif(os.name == "nt", reason="source command is Unix-only")
def test_run_source_missing_file(tmp_path):
    """Test that source command raises FileNotFoundError for missing files."""
    lusfile = LusFile("")
    cwd = os.getcwd()

    try:
        os.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            lusfile.run(["source", "nonexistent.sh"], {})
    finally:
        os.chdir(cwd)


@pytest.mark.skipif(os.name == "nt", reason="source command is Unix-only")
def test_run_source_no_arguments():
    """Test that source command requires a script argument."""
    lusfile = LusFile("")

    with pytest.raises(ValueError, match="requires a script file"):
        lusfile.run(["source"], {})


@pytest.mark.skipif(os.name == "nt", reason="source command is Unix-only")
def test_run_source_environment_variables(tmp_path):
    """Test that source command captures and persists environment variable changes."""
    lusfile = LusFile("")
    cwd = os.getcwd()

    try:
        os.chdir(tmp_path)
        script = tmp_path / "setenv.sh"
        script.write_text(
            "export MY_SOURCE_VAR=hello_world\nexport ANOTHER_SOURCE_VAR=test123\n"
        )

        if "MY_SOURCE_VAR" in os.environ:
            del os.environ["MY_SOURCE_VAR"]
        if "ANOTHER_SOURCE_VAR" in os.environ:
            del os.environ["ANOTHER_SOURCE_VAR"]

        lusfile.run(["source", str(script)], {})

        assert os.environ.get("MY_SOURCE_VAR") == "hello_world"
        assert os.environ.get("ANOTHER_SOURCE_VAR") == "test123"

        del os.environ["MY_SOURCE_VAR"]
        del os.environ["ANOTHER_SOURCE_VAR"]
    finally:
        os.chdir(cwd)


@pytest.mark.skipif(os.name != "nt", reason="test Windows behavior")
def test_run_source_ignored_on_windows(tmp_path):
    """Test that source command is silently ignored on Windows platforms."""
    lusfile = LusFile("")
    cwd = os.getcwd()

    try:
        os.chdir(tmp_path)
        script = tmp_path / "test.sh"
        script.write_text("export FOO=bar\n")

        lusfile.run(["source", str(script)], {})
    finally:
        os.chdir(cwd)
