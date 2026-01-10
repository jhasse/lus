import os
import subprocess
import sys


def lus(*args):
    """Run the lus command with the given arguments."""
    return subprocess.run(
        [sys.executable, "-m", "lus"] + list(args),
        capture_output=True,
        text=True,
        env=os.environ | {"PYTHONPATH": os.path.join(os.path.dirname(__file__), "..")},
    )


def test_default():
    os.chdir(os.path.join(os.path.dirname(__file__), "default"))

    result = lus()
    assert result.stderr == ""
    assert result.stdout == "foo\n"
    assert result.returncode == 0

    result = lus("foo")
    assert result.stderr == ""
    assert result.stdout == "foo\n"
    assert result.returncode == 0

    result = lus("foo", "additional arg")
    assert result.stderr == ""
    assert result.stdout == "foo\nadditional arg\n"
    assert result.returncode == 0


def test_args():
    os.chdir(os.path.join(os.path.dirname(__file__), "args"))

    result = lus("forward", "print('Hello, World!')")
    assert result.stderr == ""
    assert result.stdout == "Hello, World!\n"
    assert result.returncode == 0

    result = lus("forward", "print('Hello,", "World!')")
    assert (
        result.stderr
        == """  File "<string>", line 1
    print('Hello,
          ^
SyntaxError: unterminated string literal (detected at line 1)
"""
    )
    assert result.stdout == ""
    assert result.returncode == 1

    result = lus("inside", "['x', 'y']")
    assert result.stderr == ""
    assert result.stdout == "x y\n"
    assert result.returncode == 0

    result = lus("unused", "foo")
    assert result.stderr == ""
    assert result.stdout == "\x1b[1;31merror:\x1b[0m Unexpected argument: foo\n"
    assert result.returncode == 1

    result = lus("count", "a", "b", "c")
    assert result.stderr == ""
    assert result.stdout == "4\n"
    assert result.returncode == 0

    result = lus("count")
    assert result.stderr == ""
    assert result.stdout == "1\n"
    assert result.returncode == 0

    result = lus("multiple", "['arg1',", "'arg2']")
    assert result.stderr == ""
    assert result.stdout == "arg1 arg2\n3\n"
    assert result.returncode == 0


def test_subcommand_env_var():
    os.chdir(os.path.join(os.path.dirname(__file__), "subcommand-env-var"))

    result = lus("cmd1")
    assert result.stderr == ""
    assert result.stdout == "Subcommand cmd1\n1: $subcommand is: \n"
    assert result.returncode == 0

    result = lus("cmd2")
    assert result.stderr == ""
    assert result.stdout == "Subcommand cmd2\n2: $subcommand is: \n"
    assert result.returncode == 0

    result = lus()
    assert result.stderr == ""
    assert result.stdout == "Subcommand \nSubcommand cmd3\nDefault subcommand\n"
    assert result.returncode == 0

    result = lus("cmd1", "cmd4")
    assert result.stderr == ""
    assert (
        result.stdout
        == "Subcommand cmd1\n1: $subcommand is: cmd4\n4: $subcommand is: \n"
    )
    assert result.returncode == 0


def test_exit():
    os.chdir(os.path.join(os.path.dirname(__file__), "exit"))

    result = lus("subcommand")
    assert result.stderr == ""
    assert (
        result.stdout
        == "Inside subcommand\nAfter subcommand, should be printed because exit of previous line was 0\n"
    )
    assert result.returncode == 0

    result = lus("subcommand-fail")
    assert result.stderr == ""
    assert result.stdout == "Inside subcommand-fail\n"
    assert result.returncode == 42


def test_just_example():
    os.chdir(os.path.join(os.path.dirname(__file__), "just-example"))
    result = lus("non_existing")
    assert result.stderr == ""
    assert (
        result.stdout
        == """\x1b[1;31merror:\x1b[0m Unknown subcommand non_existing not one of:
    \x1b[1;34mb\x1b[0m
    \x1b[1;34mbuild\x1b[0m
    \x1b[1;34mtest-all\x1b[0m
    \x1b[1;34mtest\x1b[0m
"""
    )
    assert result.returncode == 1


def test_print_commands():
    os.chdir(os.path.join(os.path.dirname(__file__), "print-commands"))
    result = lus("verbose")
    assert result.stderr == ""
    assert (
        result.stdout
        == """echo 'Shows this text and the echo command'
Shows this text and the echo command
"""
    )
    assert result.returncode == 0

    result = lus("silent")
    assert result.stderr == ""
    assert result.stdout == "Only shows this text, not the echo command\n"
    assert result.returncode == 0


def test_error():
    os.chdir(os.path.join(os.path.dirname(__file__), "errors"))
    result = lus()
    assert result.stderr == "\x1b[1;31merror:\x1b[0m Duplicate node name 'a'\n"
    assert result.stdout == ""
    assert result.returncode == 1


def test_invocation_directory():
    test_dir = os.path.join(os.path.dirname(__file__), "invocation-directory")
    original_cwd = os.getcwd()
    try:
        os.chdir(os.path.join(test_dir, "empty-folder"))
        result = lus("show-invocation")
        assert result.stderr == ""
        assert (
            result.stdout
            == f"Invocation directory: {test_dir}/empty-folder\nempty-folder\nlus.kdl\n"
        )
        assert result.returncode == 0
    finally:
        os.chdir(original_cwd)
