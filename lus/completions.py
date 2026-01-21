"""Shell completion scripts for lus."""

BASH_COMPLETION = """
_lus_completions() {
    local cur prev
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # lus options
    if [[ "$cur" == -* ]]; then
        COMPREPLY=($(compgen -W "-l --list --completions --version --help" -- "$cur"))
        return
    fi

    # Complete shell names after --completions
    if [[ "$prev" == "--completions" ]]; then
        COMPREPLY=($(compgen -W "bash zsh fish powershell" -- "$cur"))
        return
    fi

    # If we already have a subcommand (more than 1 non-option arg), complete files/folders
    local arg_count=0
    for word in "${COMP_WORDS[@]:1:COMP_CWORD-1}"; do
        [[ "$word" != -* ]] && ((arg_count++))
    done

    if [[ $arg_count -gt 0 ]]; then
        COMPREPLY=($(compgen -f -- "$cur"))
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
        '--list[List available subcommands]'
        '--completions[Generate shell completion script]:shell:(bash zsh fish powershell)'
        '--version[Show version]'
        '--help[Show help]'
    )

    # Get subcommands from lus -l
    if [[ -f lus.kdl ]] || _lus_find_kdl; then
        subcommands=(${(f)"$(lus -l 2>/dev/null | tail -n +2 | awk '{print $1}' | sed 's/\\x1b\\[[0-9;]*m//g')"})
    fi

    _arguments -s \\
        $options \\
        '1:subcommand:($subcommands)' \\
        '*:file:_files'
}

_lus_find_kdl() {
    local dir="$PWD"
    while [[ "$dir" != "/" ]]; do
        [[ -f "$dir/lus.kdl" ]] && return 0
        dir="${dir:h}"
    done
    return 1
}

compdef _lus lus
"""

FISH_COMPLETION = """
# Fish completion for lus

function __lus_subcommands
    lus -l 2>/dev/null | tail -n +2 | awk '{print $1}' | sed 's/\\x1b\\[[0-9;]*m//g'
end

function __lus_needs_subcommand
    set -l cmd (commandline -opc)
    # Check if we only have 'lus' or 'lus' with options (starting with -)
    for arg in $cmd[2..-1]
        if not string match -q -- '-*' $arg
            return 1
        end
    end
    return 0
end

# Options
complete -c lus -s l -l list -d "List available subcommands"
complete -c lus -l completions -xa "bash zsh fish powershell" -d "Generate shell completion script"
complete -c lus -l version -d "Show version"
complete -c lus -l help -d "Show help"

# Subcommands (only when no subcommand given yet)
complete -c lus -n __lus_needs_subcommand -f -a "(__lus_subcommands)" -d "Subcommand"

# File completions after subcommand
complete -c lus -n "not __lus_needs_subcommand" -F
"""

POWERSHELL_COMPLETION = """
# PowerShell completion for lus

Register-ArgumentCompleter -Native -CommandName lus -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)

    $options = @('-l', '--list', '--completions', '--version', '--help')

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

    # Count non-option arguments (excluding 'lus' itself)
    $argCount = 0
    foreach ($word in $words | Select-Object -Skip 1) {
        if (-not $word.Extent.Text.StartsWith('-')) {
            $argCount++
        }
    }

    # If we already have a subcommand, complete files/folders
    if ($argCount -gt 0) {
        Get-ChildItem -Path "$wordToComplete*" 2>$null | ForEach-Object {
            $name = $_.Name
            $type = if ($_.PSIsContainer) { 'ProviderContainer' } else { 'ProviderItem' }
            [System.Management.Automation.CompletionResult]::new($name, $name, $type, $name)
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
