#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"

echo -e "\033[1;33m☕ Installing Roblox Caffeine...\033[0m"

# 1. Ensure ~/.local/bin exists
mkdir -p "${BIN_DIR}"

# 2. Link executable
chmod +x "${SCRIPT_DIR}/roblox_caffeine.py"
ln -sf "${SCRIPT_DIR}/roblox_caffeine.py" "${BIN_DIR}/roblox-caffeine"
echo -e "\033[32m✔ Symlinked executable to ${BIN_DIR}/roblox-caffeine\033[0m"

# 3. Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    echo -e "\033[33m⚠ Note: Make sure ${BIN_DIR} is in your PATH by adding this to your ~/.bashrc or ~/.zshrc:\033[0m"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# 4. Optional Udev Rules setup
echo ""
echo -e "\033[1mTo configure /dev/uinput permissions (run without sudo):\033[0m"
echo "  sudo usermod -aG input \$USER"
echo "  sudo cp \"${SCRIPT_DIR}/99-uinput.rules\" /etc/udev/rules.d/"
echo "  sudo udevadm control --reload-rules && sudo udevadm trigger"
echo "  sudo modprobe uinput"
echo ""
echo -e "\033[1;32m✔ Installation complete! Run 'roblox-caffeine' to start.\033[0m"
