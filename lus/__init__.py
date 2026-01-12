import subprocess
import sys
import os

from kdl.errors import ParseError

from .LusFile import LusFile
from .completions import get_completion_script


def main():
    # Handle --completions flag before looking for lus.kdl
    if len(sys.argv) >= 2 and sys.argv[1] == "--completions":
        if len(sys.argv) < 3:
            print("Usage: lus --completions <shell>", file=sys.stderr)
            print("Supported shells: bash, zsh, fish, powershell", file=sys.stderr)
            sys.exit(1)
        shell = sys.argv[2]
        try:
            print(get_completion_script(shell))
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    try:
        invocation_directory = os.getcwd()
        MAX_DEPTH = 50
        current_filesystem = os.stat(".").st_dev
        for i in range(MAX_DEPTH):
            try:
                with open("lus.kdl", "r") as f:
                    content = f.read()
            except FileNotFoundError as e:
                if current_filesystem != os.stat("..").st_dev:
                    raise e
                cwd = os.getcwd()
                os.chdir("..")
                if cwd == os.getcwd():
                    raise e
            else:
                break

        file = LusFile(content, invocation_directory)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except FileNotFoundError as e:
        print(f"\x1b[1;31merror:\x1b[0m {e.strerror}: {e.filename}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
    except ParseError as e:
        print(f"\x1b[1;31merror:\x1b[0m lus.kdl:{e}", file=sys.stderr)
        sys.exit(1)
