"""Shell completion scripts for lus."""

BASH_COMPLETION = """
_lus_completions() {
    local cur prev
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # lus options
    if [[ "$cur" == -* ]]; then
        COMPREPLY=($(compgen -W "-l --completions" -- "$cur"))
        return
    fi

    # Complete shell names after --completions
    if [[ "$prev" == "--completions" ]]; then
        COMPREPLY=($(compgen -W "bash zsh fish powershell" -- "$cur"))
        return
    fi

    # Get subcommands from lus -l
    local subcommands
    subcommands=$(lus -l 2>/dev/null | tail -n +2 | awk '{print $1}' | sed 's/\\x1b\\[[0-9;]*m//g')

    if [[ -n "$subcommands" ]]; then
        COMPREPLY=($(compgen -W "$subcommands" -- "$cur"))
    fi
}

complete -F _lus_completions lus
"""

ZSH_COMPLETION = """
#compdef lus

_lus() {
    local -a subcommands
    local -a options

    options=(
        '-l[List available subcommands]'
        '--completions[Generate shell completion script]:shell:(bash zsh fish powershell)'
    )

    # Get subcommands from lus -l
    if [[ -f lus.kdl ]] || _lus_find_kdl; then
        subcommands=(${(f)"$(lus -l 2>/dev/null | tail -n +2 | awk '{print $1}' | sed 's/\\x1b\\[[0-9;]*m//g')"})
    fi

    _arguments -s \\
        $options \\
        '*:subcommand:($subcommands)'
}

_lus_find_kdl() {
    local dir="$PWD"
    while [[ "$dir" != "/" ]]; do
        [[ -f "$dir/lus.kdl" ]] && return 0
        dir="${dir:h}"
    done
    return 1
}

_lus "$@"
"""

FISH_COMPLETION = """
# Fish completion for lus

function __lus_subcommands
    lus -l 2>/dev/null | tail -n +2 | awk '{print $1}' | sed 's/\\x1b\\[[0-9;]*m//g'
end

# Disable file completions
complete -c lus -f

# Options
complete -c lus -s l -d "List available subcommands"
complete -c lus -l completions -xa "bash zsh fish powershell" -d "Generate shell completion script"

# Subcommands
complete -c lus -a "(__lus_subcommands)" -d "Subcommand"
"""

POWERSHELL_COMPLETION = """
# PowerShell completion for lus

Register-ArgumentCompleter -Native -CommandName lus -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)

    $options = @('-l', '--completions')

    # If completing an option
    if ($wordToComplete -like '-*') {
        $options | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }
        return
    }

    # If previous word was --completions, complete shell names
    $words = $commandAst.CommandElements
    if ($words.Count -ge 2 -and $words[-2].Extent.Text -eq '--completions') {
        @('bash', 'zsh', 'fish', 'powershell') | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }
        return
    }

    # Get subcommands from lus -l
    try {
        $output = lus -l 2>$null
        if ($output) {
            $output | Select-Object -Skip 1 | ForEach-Object {
                # Extract first word and strip ANSI codes
                $line = $_ -replace '\\x1b\\[[0-9;]*m', ''
                $subcommand = ($line -split '\\s+')[0]
                if ($subcommand -and $subcommand -like "$wordToComplete*") {
                    [System.Management.Automation.CompletionResult]::new($subcommand, $subcommand, 'Command', $subcommand)
                }
            }
        }
    } catch {
        # Silently ignore errors
    }
}
"""


def get_completion_script(shell: str) -> str:
    """Return the completion script for the given shell."""
    scripts = {
        "bash": BASH_COMPLETION.strip(),
        "zsh": ZSH_COMPLETION.strip(),
        "fish": FISH_COMPLETION.strip(),
        "powershell": POWERSHELL_COMPLETION.strip(),
    }
    if shell not in scripts:
        raise ValueError(
            f"Unknown shell: {shell}. Supported shells: bash, zsh, fish, powershell"
        )
    return scripts[shell]
