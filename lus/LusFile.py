import os
import shlex
import shutil
import subprocess
import sys
import ckdl
import expandvars

class Environment:
    def __init__(self, variables: dict[str, str]):
        self.args_used = False
        self.variables = variables
        assert "args" in variables

    def get(self, key: str, fallback: str = None) -> str:
        if key in self.variables:
            if key == "args":
                self.args_used = True
            return self.variables[key]
        return os.environ.get(key, fallback)

class LusFile:
    def __init__(self, content: str):
        self.main_lus_kdl = ckdl.parse(content).nodes
        self.print_commands = False
        self.local_variables = {}
        self._old_working_directory = os.getcwd()

        self.check_args(self.main_lus_kdl, sys.argv[1:], True)

    def print_command(self, args: list[str]):
        if self.print_commands:
            print(f"\x1b[1;34m$ {shlex.join(args)}\x1b[0m")

    def run(self, args: list[str], properties: dict[str, str]):
        if args[0] == "exit":
            raise SystemExit(args[1])
        elif args[0] == "cd":
            self.print_command(args)
            if len(args) == 2 and args[1] == "-":
                os.chdir(self._old_working_directory)
                return
            self._old_working_directory = os.getcwd()
            os.chdir(args[1])
        elif args[0] == "test":
            if args[2] in ["&&", "||"]:
                args.insert(2, "")
            if args[1] == "-f" or args[1] == "-d":
                exists = os.path.exists(args[2])
                if (
                    not exists
                    or (args[1] == "-f" and not os.path.isfile(args[2]))
                    or (args[1] == "-d" and not os.path.isdir(args[2]))
                ):
                    if len(args) > 3 and args[3] == "||":
                        self.run(args[4:], properties)
                    else:
                        raise SystemExit(1)
            elif args[1] == "-z" and len(args) >= 4 and args[3] in ["&&", "||"]:
                empty = len(args[2]) == 0
                if args[3] == "&&" and empty:
                    self.run(args[4:], properties)
                elif args[3] == "||" and not empty:
                    self.run(args[4:], properties)
            else:
                raise NotImplementedError(f"test {args[1:]} not implemented")
        elif args[0] == "lus":
            old_cwd = os.getcwd()
            # print_command(args)
            try:
                self.check_args(self.main_lus_kdl, args[1:], True)
            except SystemExit as e:
                if e.code != 0:
                    raise SystemExit(e.code)
            finally:
                os.chdir(old_cwd)
        elif args[0] == "export":
            self.print_command(args + [f"{k}={v}" for k, v in properties.items()])
            os.environ.update(properties)
        elif args[0] == "set":
            global print_commands
            if args[1] == "-x":
                print_commands = True
            elif args[1] == "+x":
                print_commands = False
            else:
                raise NotImplementedError(f"set {args[1]} not implemented")
        elif "/" in args[0] and not os.path.isabs(args[0]):
            self.print_command(args)
            subprocess.check_call([os.path.join(os.getcwd(), args[0])] + args[1:])
        else:
            if not shutil.which(args[0]): # check if args[0] is in PATH
                if sys.platform == "darwin": # only macOS
                    brew_path = shutil.which("brew")
                    if brew_path:
                        result = subprocess.check_output(
                            [brew_path, "which-formula", args[0]],
                            text=True
                        )
                        formula = result.strip()
                        if formula:
                            # ask [Y/n] if to install it now:
                            response = input(
                                f"\x1b[1;33mwarning:\x1b[0m Command '{args[0]}' not found. "
                                f"It is provided by the Homebrew package '\x1b[1;34m{formula}\x1b[0m'. "
                                "Do you want to install it now? [Y/n] "
                            )
                            if response.lower() in ["", "y", "yes"]:
                                self.print_command([brew_path, "install", formula])
                                subprocess.check_call([brew_path, "install", formula])
            self.print_command(args)
            subprocess.check_call(args)

    def check_args(self, nodes, args: list[str], check_if_args_handled: bool):
        # Flags for this subcommand, i.e. ["--release"]
        flags = []

        # Everything after the last flag. For example, if the command is `lus build --release foo bar
        # -v`, then this will contain `["foo", "bar", "-v"]`.
        remaining_args_without_flags = []

        for arg in args:
            if len(remaining_args_without_flags) == 0 and arg.startswith("-"):
                flags.append(arg)
            else:
                remaining_args_without_flags.append(arg)
        remaining_args = [str(x) for x in args]

        subcommand = (
            remaining_args_without_flags[0]
            if remaining_args_without_flags
            else ""
        )
        environment = Environment({"args": " ".join(remaining_args), "subcommand": subcommand})

        child_names = set()
        for i, child in enumerate(nodes):
            if child.name == "$" or child.name == "-":
                if len(child.args) > 0:
                    cmd = []
                    for arg in child.args:
                        if arg == "$args":
                            # special case because it won't be passed as one argument with spaces
                            environment.args_used = True
                            cmd.extend(remaining_args)
                            continue
                        cmd.append(expandvars.expand(str(arg), environ=environment, nounset=True))
                    if environment.args_used:
                        remaining_args = []
                    self.run(cmd, child.properties)
                else:
                    self.local_variables.update(child.properties)
                continue
            if child.name in child_names:
                print(f"\x1b[1;31merror:\x1b[0m Duplicate node name '{child.name}'", file=sys.stderr)
                raise SystemExit(1)
            child_names.add(child.name)
            if child.name == subcommand:
                try:
                    remaining_args.remove(subcommand)
                except ValueError:
                    pass # if there was a script line before that used $args, it may already be removed
                self.check_args(child.children, remaining_args, i == len(nodes) - 1)
                remaining_args = []
            elif child.name in flags:
                remaining_args.remove(child.name)
                self.check_args(child.children, remaining_args_without_flags, False)
        if check_if_args_handled and len(remaining_args) > 0:
            available_subcommands = [
                child.name
                for child in nodes
                if len(child.name) > 0
                and child.name != "$"
                and child.name[0] != "-"
                and child.name != ""
            ]
            if len(available_subcommands) == 0:
                print(
                    f"\x1b[1;31merror:\x1b[0m Unexpected argument: {shlex.join(remaining_args)}"
                )
            else:
                print(
                    f"\x1b[1;31merror:\x1b[0m Unknown subcommand {shlex.quote(subcommand)} not one of:"
                )
                for available_subcommand in available_subcommands:
                    print(f"    \x1b[1;34m{available_subcommand}\x1b[0m")
            raise SystemExit(1)
