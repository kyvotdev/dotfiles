#!/bin/bash
set -euo pipefail
profile=${1:-all}
base=(neovim git ripgrep fd tree-sitter-cli gcc make unzip)
python_tools=(python python-pytest python-debugpy nodejs pyright ruff)
web_tools=(nodejs npm typescript typescript-language-server vscode-json-languageserver vscode-html-languageserver vscode-css-languageserver yaml-language-server prettier)
systems_tools=(clang gdb rust go rust-analyzer gopls delve)
extra_tools=(lua-language-server stylua bash-language-server shfmt marksman taplo-cli dockerfile-language-server ruby-lsp)
packages=("${base[@]}")
case "$profile" in
    core) ;;
    python) packages+=("${python_tools[@]}") ;;
    web) packages+=("${web_tools[@]}") ;;
    systems) packages+=("${systems_tools[@]}") ;;
    all) packages+=("${python_tools[@]}" "${web_tools[@]}" "${systems_tools[@]}" "${extra_tools[@]}") ;;
    *) echo 'Usage: install-dev-tools.sh core|python|web|systems|all [--print]' >&2; exit 2 ;;
esac
if [[ ${2:-} == --print ]]; then printf '%s\n' "${packages[@]}"; exit; fi
printf 'Installing the %s development profile through pacman.\n' "$profile"
sudo pacman -Syu --needed "${packages[@]}"
python3 "$HOME/.config/nvim/scripts/install-plugins.py"
printf '%s\n' 'Restart Neovim, then run :PixelParsers and :PixelTools.'
