# lus

`lus` is a task runner similar to [just](https://just.systems). It's key differentiators are:

* No DSL, `lus` uses the existing [KDL](https://kdl.dev)
* Runs tasks directly without a shell
* Comes with a simple built-in shell, so it works out-of-the-box on Windows
* Less features

```kdl
b {
    - lus build
}

- host="$(uname -a)"

// build main
build {
    - cc *.a -o main
}

// test everything
test-all {
    - lus build
    - "./test" --all
}

// run a specific test
test {
    - lus build
    - "./test" --test $args
}
```

## Special environment variables

| Variable                   | Description                        |
|----------------------------|------------------------------------|
| `$args`                    | Additional arguments passed to lus |
| `$subcommand`              | Current subcommand being executed  |
| `$flags`                   | Arguments starting with `--`       |
| `$invocation_directory`    | Directory where `lus` was invoked  |

## Shell Completions

`lus` supports tab completion for bash, zsh, fish, and PowerShell. Add one of the following to your shell configuration:

**Bash** (`~/.bashrc`):
```bash
eval "$(lus --completions bash)"
```

**Zsh** (`~/.zshrc`):
```bash
eval "$(lus --completions zsh)"
```

**Fish** (`~/.config/fish/config.fish`):
```fish
lus --completions fish | source
```

**PowerShell** (`$PROFILE`):
```powershell
Invoke-Expression (& lus --completions powershell)
```

# Development

Run unit and integration tests:

```
python -m venv .venv
. .venv/bin/activate.fish
pip install kdl-py expandvars pytest
pytest
```
