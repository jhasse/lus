import os
import subprocess
import sys


def test_just_example():
    os.chdir(os.path.join(os.path.dirname(__file__), "just-example"))
    result = subprocess.run(
        [sys.executable, "-m", "lus", "non_existing"],
        capture_output=True,
        text=True,
        env=os.environ | {"PYTHONPATH": os.path.join(os.path.dirname(__file__), "..")},
    )
    assert result.returncode == 1
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
