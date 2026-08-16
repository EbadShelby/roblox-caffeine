#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"

echo -e "\033[1;33m☕ Installing Roblox Caffeine...\033[0m"

# 1. Check Python & evdev dependency
if ! command -v python3 &>/dev/null; then
    echo -e "\033[91m✕ Python 3 is required but not installed.\033[0m"
    exit 1
fi

if ! python3 -c "import evdev" &>/dev/null; then
    echo -e "\033[33m⚠ Python 'evdev' module is missing. Install it with:\033[0m"
    echo "  Fedora:  sudo dnf install python3-evdev"
    echo "  Arch:    sudo pacman -S python-evdev"
    echo "  Ubuntu:  sudo apt install python3-evdev"
    echo "  Pip:     pip install evdev"
    echo ""
fi

# 2. Ensure ~/.local/bin exists
mkdir -p "${BIN_DIR}"

# 3. Link executable
chmod +x "${SCRIPT_DIR}/roblox_caffeine.py"
ln -sf "${SCRIPT_DIR}/roblox_caffeine.py" "${BIN_DIR}/roblox-caffeine"
echo -e "\033[32m✔ Symlinked executable to ${BIN_DIR}/roblox-caffeine\033[0m"

# 4. Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    echo -e "\033[33m⚠ Note: Make sure ${BIN_DIR} is in your PATH by adding this to your ~/.bashrc or ~/.zshrc:\033[0m"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo -e "\033[1;32m✔ Installation complete!\033[0m"
echo -e "Next step: Run \033[1;36mroblox-caffeine --setup\033[0m to configure /dev/uinput permissions."
