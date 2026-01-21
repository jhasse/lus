import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import expandvars
import kdl
from termcolor import colored


@dataclass
class NormalizedNode:
    name: str
    args: List[Any]
    properties: Dict[str, Any]
    children: List["NormalizedNode"]


def _normalize_value(value):
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _normalize_node(node) -> NormalizedNode:
    props = getattr(node, "properties", getattr(node, "props", {}))
    children = getattr(node, "children", getattr(node, "nodes", []))
    return NormalizedNode(
        name=getattr(node, "name", ""),
        args=[_normalize_value(arg) for arg in getattr(node, "args", [])],
        properties={k: _normalize_value(v) for k, v in props.items()},
        children=[_normalize_node(child) for child in children],
    )


def _normalize_nodes(nodes) -> List[NormalizedNode]:
    return [_normalize_node(node) for node in nodes]


_KDL_PATCHED = False


def _ensure_kdl_supports_bare_identifiers():
    global _KDL_PATCHED
    if _KDL_PATCHED:
        return

    from kdl import converters
    from kdl import parsefuncs
    from kdl.errors import ParseError, ParseFragment
    from kdl.result import Failure, Result
    from kdl import types as kdl_types

    def parse_value_with_bare_identifiers(stream, start):
        tag, i = parsefuncs.parseTag(stream, start)
        if tag is Failure:
            tag = None

        value_start = i
        val, i = parsefuncs.parseNumber(stream, i)
        if val is Failure:
            val, i = parsefuncs.parseKeyword(stream, i)
            if val is Failure:
                val, i = parsefuncs.parseString(stream, i)
                if val is Failure:
                    ident, ident_end = parsefuncs.parseIdent(stream, i)
                    if ident is not Failure:
                        val = kdl_types.String(ident)
                        i = ident_end

        if val is not Failure:
            val.tag = tag
            for key, converter in stream.config.valueConverters.items():
                if val.matchesKey(key):
                    val = converter(
                        val,
                        ParseFragment(stream[value_start:i], stream, i),
                    )
                    if val == NotImplemented:
                        continue
                    else:
                        break
            else:
                if tag is None and stream.config.nativeUntaggedValues:
                    val = val.value
                if tag is not None and stream.config.nativeTaggedValues:
                    val = converters.toNative(
                        val,
                        ParseFragment(stream[value_start:i], stream, i),
                    )
            return Result((None, val), i)

        if stream[i] == "'":
            raise ParseError(stream, i, "KDL strings use double-quotes.")

        ident, _ = parsefuncs.parseBareIdent(stream, i)
        if ident is not Failure and ident.lower() in ("true", "false", "null"):
            raise ParseError(stream, i, "KDL keywords are lower-case.")

        if tag is not None:
            raise ParseError(stream, i, "Found a tag, but no value following it.")
        return Result.fail(start)

    parsefuncs.parseValue = parse_value_with_bare_identifiers
    _KDL_PATCHED = True


class Environment:
    def __init__(self, variables: Dict[str, str]):
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
    @staticmethod
    def _strip_ansi(text: str) -> str:
        # Remove ANSI escape codes for visible width calculation
        return re.sub(r"\x1b\[[0-9;]*m", "", text)

    def __init__(
        self, content: str, invocation_directory: str = None, args: List[str] = None
    ):
        _ensure_kdl_supports_bare_identifiers()
        self._raw_content = content
        self.main_lus_kdl = _normalize_nodes(kdl.parse(content).nodes)
        self.print_commands = True
        self.local_variables = {}
        self._piped = not sys.stdout.isatty()
        self._old_working_directory = os.getcwd()
        self._invocation_directory = invocation_directory or os.getcwd()
        self._subcommand_comments = self._extract_top_level_comments(content)
        self._aliases = self._compute_aliases(self.main_lus_kdl)

        if self.main_lus_kdl:
            self.check_args(
                self.main_lus_kdl, args if args is not None else sys.argv[1:], True
            )

    def _extract_top_level_comments(self, content: str) -> Dict[str, str]:
        comments = {}
        pending: List[str] = []
        depth = 0

        for line in content.splitlines():
            stripped = line.strip()

            if stripped.startswith("//"):
                if depth == 0:
                    pending.append(stripped[2:].strip())
                continue

            if depth == 0 and stripped and not stripped.startswith(("{", "}")):
                # Grab the token up to whitespace or '{'
                token = re.split(r"\s|{", stripped, maxsplit=1)[0]
                if token and pending:
                    comments[token] = " ".join(pending)
                pending = []

            depth += line.count("{") - line.count("}")

            # Only keep pending comments for top-level declarations
            if depth != 0:
                pending = []

        return comments

    def _compute_aliases(self, nodes: List[NormalizedNode]) -> Dict[str, str]:
        aliases: Dict[str, str] = {}
        for node in nodes:
            if node.name in ("", "$", "-"):
                continue
            if len(node.children) != 1:
                continue
            child = node.children[0]
            if child.properties or node.properties:
                continue
            # Handle both "$ lus build" and "lus build" formats
            if child.name in ("$", "-"):
                args = child.args
                if len(args) >= 2 and args[0] == "lus" and isinstance(args[1], str):
                    aliases[node.name] = args[1]
            elif child.name == "lus" and len(child.children) == 0:
                args = child.args
                if len(args) >= 1 and isinstance(args[0], str):
                    aliases[node.name] = args[0]
        return aliases

    def print_command(self, args: List[str]):
        if self.print_commands:
            self._print(colored(shlex.join(args), attrs=["bold"]))

    def _print(self, message: str):
        if self._piped:
            # strip ANSI escape codes
            ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
            message = ansi_escape.sub('', message)
        print(message, flush=True)

    def run(self, args: List[str], properties: Dict[str, str]):
        if "&&" in args or "||" in args:
            return self._run_chained(args, properties)
        status, _ = self._run_single(args, properties)
        if status != 0:
            raise SystemExit(status)

    def _run_chained(self, args: List[str], properties: Dict[str, str]):
        segments = []
        operators = []
        current = []

        for arg in args:
            if arg in ("&&", "||"):
                if len(current) == 0:
                    raise SystemExit(1)
                segments.append(current)
                operators.append(arg)
                current = []
            else:
                current.append(arg)

        if len(current) == 0:
            raise SystemExit(1)
        segments.append(current)

        last_status = 0

        for i, segment in enumerate(segments):
            try:
                status, condition = self._run_single(segment, properties)
            except SystemExit as e:
                status = e.code
                condition = status == 0
                if len(segment) > 0 and segment[0] == "exit":
                    raise
            except subprocess.CalledProcessError as e:
                status = e.returncode
                condition = False

            last_status = status

            if i < len(operators):
                op = operators[i]
                if op == "&&":
                    if condition:
                        continue
                    if status != 0:
                        raise SystemExit(status)
                    return
                if op == "||":
                    if condition:
                        return
                    continue

        if last_status != 0:
            raise SystemExit(last_status)

    def _run_single(
        self, args: List[str], properties: Dict[str, str]
    ) -> Tuple[int, bool]:
        if args[0] == "exit":
            code = args[1] if len(args) > 1 else 0
            try:
                code = int(code)
            except (ValueError, TypeError):
                pass
            raise SystemExit(code)
        elif args[0] == "cd":
            self.print_command(args)
            if len(args) == 2 and args[1] == "-":
                os.chdir(self._old_working_directory)
                return 0, True
            self._old_working_directory = os.getcwd()
            os.chdir(args[1])
            return 0, True
        elif args[0] == "test":
            if len(args) < 3:
                raise NotImplementedError(f"test {args[1:]} not implemented")
            if args[1] == "-f" or args[1] == "-d":
                exists = os.path.exists(args[2])
                if (
                    not exists
                    or (args[1] == "-f" and not os.path.isfile(args[2]))
                    or (args[1] == "-d" and not os.path.isdir(args[2]))
                ):
                    raise SystemExit(1)
                return 0, True
            elif args[1] == "-z":
                empty = len(args[2]) == 0
                if empty:
                    return 0, True
                return 0, False
            elif args[1] == "-n":
                not_empty = len(args[2]) > 0
                if not_empty:
                    return 0, True
                return 0, False
            else:
                raise NotImplementedError(f"test {args[1:]} not implemented")
            return 0, True
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
            return 0, True
        elif args[0] == "export":
            self.print_command(args + [f"{k}={v}" for k, v in properties.items()])
            os.environ.update(properties)
            return 0, True
        elif args[0] == "set":
            if args[1] == "-x":
                self.print_commands = True
            elif args[1] == "+x":
                self.print_commands = False
            else:
                raise NotImplementedError(f"set {args[1]} not implemented")
            return 0, True
        elif "/" in args[0] and not os.path.isabs(args[0]):
            self.print_command(args)
            subprocess.check_call([os.path.join(os.getcwd(), args[0])] + args[1:])
            return 0, True
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
                                f"{colored('warning:', 'yellow', attrs=['bold'])} Command '{args[0]}' not found. "
                                f"It is provided by the Homebrew package '{colored(formula, 'blue', attrs=['bold'])}'. "
                                "Do you want to install it now? [Y/n] "
                            )
                            if response.lower() in ["", "y", "yes"]:
                                self.print_command([brew_path, "install", formula])
                                subprocess.check_call([brew_path, "install", formula])
            self.print_command(args)
            subprocess.check_call(args,
                shell=os.name == 'nt' # required to run .bat, .cmd, etc. on Windows
            )
            return 0, True

    def check_args(self, nodes, args: List[str], check_if_args_handled: bool):
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
            remaining_args_without_flags[0] if remaining_args_without_flags else ""
        )
        environment = Environment(
            {
                "args": " ".join(remaining_args),
                "subcommand": subcommand,
                "invocation_directory": self._invocation_directory,
                "flags": " ".join(flags),
            }
        )
        subcommand_executed = False

        subcommand_exists = any(
            child.name == subcommand
            for child in nodes
            if len(child.name) > 0 and child.name not in ("$", "-")
        )

        available_subcommands = [
            child.name
            for child in nodes
            if len(child.name) > 0
            and child.name not in ("$", "-")
            and child.name[0] != "-"
            and child.name != ""
        ]

        comments = self._subcommand_comments
        aliases = self._aliases

        # Build a mapping of subcommand names to their flag children
        subcommand_flags: Dict[str, List[str]] = {}
        for child in nodes:
            if (
                child.name
                and child.name not in ("$", "-")
                and not child.name.startswith("-")
            ):
                child_flags = [
                    c.name for c in child.children if c.name.startswith("--")
                ]
                subcommand_flags[child.name] = child_flags

        if "-l" in flags:
            print("Available subcommands:")
            # Compute display length including flags for proper alignment
            display_parts: List[Tuple[str, str]] = []  # (name, flags_str)
            for name in available_subcommands:
                flags_list = subcommand_flags.get(name, [])
                if flags_list:
                    flags_str = " ".join(colored(f"[{f}]", "blue") for f in flags_list)
                else:
                    flags_str = ""
                display_parts.append((name, flags_str))

            def visible_len(name, flags_str):
                # Calculate visible length (without ANSI codes)
                name_flags = name + (" " + flags_str if flags_str else "")
                return len(self._strip_ansi(name_flags))

            max_len = max(
                (visible_len(name, flags_str) for name, flags_str in display_parts),
                default=0,
            )

            for name, flags_str in display_parts:
                suffix_text = ""
                alias_target = aliases.get(name)
                comment = comments.get(name)
                if alias_target:
                    suffix_text = f"# alias for `{alias_target}`"
                elif comment:
                    suffix_text = f"# {comment}"

                name_with_flags = name + (" " + flags_str if flags_str else "")
                if suffix_text:
                    visible = self._strip_ansi(name_with_flags)
                    padding = " " * (max_len - len(visible) + 1)
                    suffix = f"{padding}{colored(suffix_text, 'green')}"
                else:
                    suffix = ""

                flags_part = " " + flags_str if flags_str else ""
                print(f"    {name}{flags_part}{suffix}")
            return

        child_names = set()
        for i, child in enumerate(nodes):
            if child.name == "$" or child.name == "-" or (len(child.children) == 0 and len(child.args) > 0):
                if len(child.args) > 0:
                    cmd = [] if child.name == "$" or child.name == "-" else [child.name]
                    for arg in child.args:
                        if arg == "$args":
                            # special case because it won't be passed as one argument with spaces
                            environment.args_used = True
                            if len(remaining_args) == 0:
                                # Only keep a placeholder when the target command needs an argument (e.g., test -n $args)
                                if len(cmd) > 0 and cmd[0] == "test":
                                    cmd.append("")
                            else:
                                cmd.extend(remaining_args)
                            continue
                        cmd.append(expandvars.expand(str(arg), environ=environment, nounset=True))
                    if subcommand_executed and len(cmd) > 1 and cmd[0] == "lus" and cmd[1] == subcommand:
                        continue
                    self.run(cmd, child.properties)
                else:
                    self.local_variables.update(child.properties)
                continue
            if len(child.children) > 0:
                if child.name in child_names:
                    print(f"{colored('error:', 'red', attrs=['bold'])} Duplicate node name '{child.name}'", file=sys.stderr)
                    raise SystemExit(1)
                child_names.add(child.name)
            if child.name == subcommand:
                try:
                    remaining_args.remove(subcommand)
                except ValueError:
                    pass # if there was a script line before that used $args, it may already be removed
                try:
                    # Once we've matched the subcommand, enforce leftover-argument checks inside it
                    self.check_args(child.children, remaining_args, True)
                    subcommand_executed = True
                except SystemExit as e:
                    if e.code != 0:
                        raise
                    subcommand_executed = True
                remaining_args = []
            elif child.name in flags:
                remaining_args.remove(child.name)
                self.check_args(child.children, remaining_args_without_flags, False)
        # If $args was used in this block, treat the arguments as consumed even if they remain
        # in the local list so subsequent commands can reuse them.
        if (
            check_if_args_handled
            and len(remaining_args) > 0
            and not environment.args_used
        ):
            if len(available_subcommands) == 0:
                print(
                    f"{colored('error:', 'red', attrs=['bold'])} Unexpected argument: {shlex.join(remaining_args)}"
                )
            else:
                print(
                    f"{colored('error:', 'red', attrs=['bold'])} Unknown subcommand {shlex.quote(subcommand)} not one of:"
                )
                for available_subcommand in available_subcommands:
                    print(
                        f"    {colored(available_subcommand, 'blue', attrs=['bold'])}"
                    )
            raise SystemExit(1)
