import subprocess
import sys
import ckdl
import os

from sly import check_args, main_sly_kdl


try:
    MAX_DEPTH = 50
    current_filesystem = os.stat(".").st_dev
    for i in range(MAX_DEPTH):
        try:
            with open("sly.kdl", "r") as f:
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

    main_sly_kdl = ckdl.parse(content).nodes

    check_args(main_sly_kdl, sys.argv[1:], True)
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
