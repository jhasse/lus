import subprocess
import sys
import ckdl
import os

from .LusFile import LusFile

try:
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

    file = LusFile(content)
except subprocess.CalledProcessError as e:
    sys.exit(e.returncode)
except FileNotFoundError as e:
    print(f"\x1b[1;31merror:\x1b[0m {e.strerror}: {e.filename}", file=sys.stderr)
    sys.exit(1)
except KeyboardInterrupt:
    sys.exit(130)
except ckdl.ParseError as e:
    print(f"\x1b[1;31merror:\x1b[0m {e}", file=sys.stderr)
    sys.exit(1)
