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

def test_error():
    os.chdir(os.path.join(os.path.dirname(__file__), "errors"))
    result = lus()
    assert result.stderr == "\x1b[1;31merror:\x1b[0m Duplicate node name 'a'\n"
    assert result.stdout == ""
    assert result.returncode == 1
