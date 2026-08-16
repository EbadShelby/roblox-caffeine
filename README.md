<div align="center">

```text
 ___  ___  ___ _    _____  __   ___   _   ___ ___ ___ ___ _  _ ___ 
| _ \/ _ \| _ ) |  / _ \ \/ /  / __| /_\ | __| __| __|_ _| \| | __|
|   / (_) | _ \ |_| (_) >  <  | (__ / _ \| _|| _|| _| | || .` | _| 
|_|_\\___/|___/____\___/_/\_\  \___/_/ \_\_| |_| |___|___|_|\_|___|
```

### ☕ Keep your Roblox window awake on Linux

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Linux](https://img.shields.io/badge/Platform-Linux%20(Wayland%20%26%20X11)-orange.svg?style=flat-square&logo=linux&logoColor=white)](https://kernel.org/)
[![Sober](https://img.shields.io/badge/Target-Sober%20%2F%20SDL2-informational.svg?style=flat-square)](https://sober.vinegarhq.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

*A minimalist, zero-focus-stealing keep-alive utility that prevents Roblox's 20-minute inactivity kick via kernel gamepad emulation.*

</div>

---

## 🌟 Why Roblox Caffeine?

Traditional anti-AFK methods on Linux (like `xdotool` auto-clickers or Lua injectors) either **break on Wayland**, **hijack your keyboard/mouse**, or **risk getting your account banned by anticheat**.

**Roblox Caffeine** takes an elegant, hardware-level approach:
- 🎮 **Native Virtual Gamepad**: Emulates a Microsoft Xbox 360 controller directly at the Linux kernel level (`/dev/uinput`).
- 🪟 **Zero Focus Stealing**: Runs completely in the background. You can type, code, or play other games while Roblox stays awake on another workspace or minimized.
- 🛡️ **100% Wayland & Niri Compatible**: Operates beneath the display server, meaning it works flawlessly on **Wayland** (Niri, GNOME, KDE, Hyprland, Sway) and **X11**.
- 🔒 **Safe & Legitimate**: Zero memory injection, zero DLL hooking, and zero client tampering.
- ⚡ **Fastfetch-Inspired CLI**: Minimalist terminal aesthetic with live countdown tickers and clean status cards.

---

## 📸 Output Preview

```text
┌────────────────────────────────────────┐
    ☕ : Roblox Caffeine
      : Virtual Xbox 360 Gamepad
    󰅐  : Interval: Every 10m
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
    ☕ : Caffeine Active #001 [05:42 PM]
      : Motion: ↗ UP-RIGHT
    󰅐  : Next: 05:52 PM (in 10m)
└────────────────────────────────────────┘
 ⠋ Next in ~9m [████░░░░░░] • Uptime: 0m
```

---

## 🚀 Installation & Setup

### 1. Install System Dependencies

Install Python and the `evdev` library for your Linux distribution:

| Distribution | Command |
| :--- | :--- |
| **Fedora / RHEL** | `sudo dnf install python3-evdev` |
| **Arch Linux / Manjaro** | `sudo pacman -S python-evdev` |
| **Ubuntu / Debian** | `sudo apt install python3-evdev` |
| **openSUSE** | `sudo zypper install python3-evdev` |
| **Universal (pip)** | `pip install -r requirements.txt` |

---

### 2. Configure `/dev/uinput` Permissions (Run without `sudo`)

To allow your non-root user to create virtual gamepad devices:

1. **Add your user to the `input` group**:
   ```bash
   sudo usermod -aG input $USER
   ```

2. **Install the udev rule** (`/etc/udev/rules.d/99-uinput.rules`):
   ```bash
   echo 'KERNEL=="uinput", GROUP="input", MODE="0660", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/99-uinput.rules
   ```

3. **Reload udev rules & load the module**:
   ```bash
   sudo udevadm control --reload-rules && sudo udevadm trigger
   sudo modprobe uinput
   ```

4. **Reboot or log out** for group permissions to apply.

---

### 3. Configure Sober (Flatpak)

If you are running **Sober** via Flatpak:

1. **Allow Sober to access hardware/input devices**:
   ```bash
   flatpak override --user --device=all org.vinegarhq.Sober
   ```

2. **Verify gamepad support in Sober configuration**:
   Ensure `"allow_gamepad_permission": true` is set in `~/.var/app/org.vinegarhq.Sober/config/sober/settings.json`:
   ```json
   {
     "allow_gamepad_permission": true
   }
   ```

---

## 🎮 Usage

### Quick Start
Clone the repository and run:
```bash
git clone https://github.com/EbadShelby/roblox-caffeine.git
cd roblox-caffeine
chmod +x roblox_caffeine.py
./roblox_caffeine.py
```

### Install as a System Command (Optional)
Run the included installer to link the binary to `~/.local/bin/roblox-caffeine`:
```bash
./install.sh
```
Now you can launch it from any terminal simply by running:
```bash
roblox-caffeine
```

### Options
```text
options:
  -h, --help            Show this help message and exit
  -i, --interval SECONDS
                        Pulse interval in seconds (default: 600s / 10m)
```

Example for a 5-minute interval:
```bash
roblox-caffeine --interval 300
```

---

## ⚙️ Running as a Systemd Background Service (Optional)

If you want Roblox Caffeine to run silently in the background:

1. Copy the systemd service file:
   ```bash
   mkdir -p ~/.config/systemd/user
   cp roblox-caffeine.service ~/.config/systemd/user/
   ```

2. Enable and start the service:
   ```bash
   systemctl --user daemon-reload
   systemctl --user enable --now roblox-caffeine.service
   ```

3. View live logs:
   ```bash
   journalctl --user -u roblox-caffeine -f
   ```

---

## 📊 Comparison with Other Solutions

| Feature | ☕ Roblox Caffeine | 🖱️ Auto-Clicker (`xdotool`) | 💉 Lua Injectors | 🔌 USB Jiggler |
| :--- | :---: | :---: | :---: | :---: |
| **Works in Background** |  **Yes** | ❌ No |  Yes | ❌ No |
| **Wayland & Niri Ready** |  **Yes** | ❌ Broken | ❌ No |  Yes |
| **No Focus Stealing** |  **Yes** | ❌ Steals input |  Yes | ❌ Hijacks mouse |
| **Anticheat Safe** |  **100% Safe** |  Safe | 🛑 **High Ban Risk** |  Safe |
| **No Extra Hardware** |  **Yes** |  Yes |  Yes | ❌ Requires Dongle |

---

## ❓ FAQ & Troubleshooting

<details>
<summary><b>Permission denied on /dev/uinput?</b></summary>

Make sure your user belongs to the `input` group (`groups $USER`) and you have applied the udev rule from Step 2. Alternatively, you can run the script temporarily with `sudo python3 roblox_caffeine.py`.
</details>

<details>
<summary><b>Does this work with native Linux games other than Roblox?</b></summary>

Yes! Any Linux application or SDL2 game that accepts gamepad input will detect the virtual Xbox 360 controller.
</details>

<details>
<summary><b>How does it avoid drifting in game?</b></summary>

Roblox Caffeine simulates a 0.3-second stick deflection and immediately returns all axes (`ABS_X`, `ABS_Y`, `ABS_RX`, `ABS_RY`) back to absolute zero `(0, 0)`, ensuring your avatar does not keep walking.
</details>

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.
