#!/usr/bin/env python3
"""
Roblox Caffeine - Minimalist Keep-Alive Utility for Linux / Sober
Periodically sends virtual gamepad button & thumbstick pulses via /dev/uinput
to prevent Roblox's 20-minute inactivity kick.
"""

import argparse
import os
import random
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta

try:
    import evdev
    from evdev import UInput, ecodes as e
except ImportError:
    print("\033[91m✕ Missing Python 'evdev' module.\033[0m")
    print("  Fedora:  sudo dnf install python3-evdev")
    print("  Arch:    sudo pacman -S python-evdev")
    print("  Ubuntu:  sudo apt install python3-evdev")
    print("  Pip:     pip install evdev")
    sys.exit(1)

# ==============================================================================
# Minimal Fastfetch Aesthetic Styling
# ==============================================================================
GRAY = '\033[90m'
CYAN = '\033[96m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
RED = '\033[91m'
BOLD = '\033[1m'
DIM = '\033[2m'
RESET = '\033[0m'
CLEAR = '\r\033[K'
WIDTH = 40

SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
STICK_DEFLECTION = 22000
DEFAULT_INTERVAL_MINUTES = 5  # 3-4 pulses inside Roblox's 20-minute window
DEVICE_WARMUP_SECONDS = 1.5   # Allow udev/SDL3/Sober to open the virtual device
DEFAULT_GAMESCOPE_RES = "1920x1080"
GAMESCOPE_UNFOCUSED_FPS = 15

BANNER_ART = r"""
 ___  ___  ___ _    _____  __   ___   _   ___ ___ ___ ___ _  _ ___ 
| _ \/ _ \| _ ) |  / _ \ \/ /  / __| /_\ | __| __| __|_ _| \| | __|
|   / (_) | _ \ |_| (_) >  <  | (__ / _ \| _|| _|| _| | || .` | _| 
|_|_\\___/|___/____\___/_/\_\  \___/_/ \_\_| |_| |___|___|_|\_|___|
"""

# Complete Microsoft Xbox 360 (xpad) profile for native SDL2 / SDL3 / Sober compatibility
CAPABILITIES = {
    e.EV_KEY: [
        e.BTN_A, e.BTN_B, e.BTN_X, e.BTN_Y,
        e.BTN_TL, e.BTN_TR, e.BTN_SELECT, e.BTN_START,
        e.BTN_MODE, e.BTN_THUMBL, e.BTN_THUMBR,
    ],
    e.EV_ABS: [
        (e.ABS_X, evdev.AbsInfo(0, -32768, 32767, 16, 128, 0)),
        (e.ABS_Y, evdev.AbsInfo(0, -32768, 32767, 16, 128, 0)),
        (e.ABS_Z, evdev.AbsInfo(0, 0, 255, 0, 0, 0)),
        (e.ABS_RX, evdev.AbsInfo(0, -32768, 32767, 16, 128, 0)),
        (e.ABS_RY, evdev.AbsInfo(0, -32768, 32767, 16, 128, 0)),
        (e.ABS_RZ, evdev.AbsInfo(0, 0, 255, 0, 0, 0)),
        (e.ABS_HAT0X, evdev.AbsInfo(0, -1, 1, 0, 0, 0)),
        (e.ABS_HAT0Y, evdev.AbsInfo(0, -1, 1, 0, 0, 0)),
    ]
}

def format_time(seconds: int) -> str:
    """Formats seconds into minutes and hours without seconds."""
    h, m = divmod(seconds // 60, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"

def print_banner():
    """Prints the Roblox Caffeine ASCII art banner and tagline."""
    print(f"\n{YELLOW}{BOLD}{BANNER_ART.strip()}{RESET}")
    print(f"{DIM}                 Keep your roblox window awake{RESET}\n")

def render_box(title_icon: str, title_text: str, key_val_pairs: list):
    """Renders a minimalist fastfetch-styled box."""
    print(f"{GRAY}┌{'─' * WIDTH}┐{RESET}")
    print(f"    {title_icon} : {title_text}")
    for icon, val in key_val_pairs:
        print(f"    {icon} : {val}")
    print(f"{GRAY}└{'─' * WIDTH}┘{RESET}")

def run_setup():
    """Automates /dev/uinput configuration with sudo."""
    print_banner()
    render_box(
        f"{YELLOW}☕{RESET}", f"{BOLD}Roblox Caffeine Setup{RESET}",
        [
            (f"{CYAN}󰅐{RESET} ", "Configuring /dev/uinput permissions..."),
        ]
    )
    print()

    user = os.environ.get("USER") or os.environ.get("LOGNAME")
    if not user:
        try:
            import pwd
            user = pwd.getpwuid(os.getuid()).pw_name
        except Exception:
            user = "root"

    udev_content = 'KERNEL=="uinput", GROUP="input", MODE="0660", TAG+="uaccess", OPTIONS+="static_node=uinput"'

    commands = [
        ("Adding user to 'input' group", ["sudo", "usermod", "-aG", "input", user]),
        ("Writing udev rule (/etc/udev/rules.d/99-uinput.rules)", ["sudo", "sh", "-c", f'echo \'{udev_content}\' > /etc/udev/rules.d/99-uinput.rules']),
        ("Loading uinput kernel module", ["sudo", "modprobe", "uinput"]),
        ("Reloading udev rules", ["sudo", "udevadm", "control", "--reload-rules"]),
        ("Applying udev rule to /dev/uinput", ["sudo", "udevadm", "trigger", "--name-match=uinput"]),
    ]

    for desc, cmd in commands:
        print(f"  {CYAN}•{RESET} {desc}...")
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print(f"\n{RED}✕ Setup failed during: {desc}{RESET}")
            return False

    print()
    render_box(
        f"{GREEN}✔{RESET}", f"{BOLD}Permissions Configured{RESET}",
        [
            (f"{YELLOW}󰋖{RESET} ", "Ready now (re-login if permission error)"),
            (f"{BLUE}☕{RESET} ", "Run: roblox-caffeine --launch"),
        ]
    )
    print()
    return True

def reset_inputs(ui: UInput):
    """Releases pulse buttons and re-centers all thumbstick axes cleanly."""
    for btn in (e.BTN_A, e.BTN_THUMBL):
        ui.write(e.EV_KEY, btn, 0)
    for axis in (e.ABS_X, e.ABS_Y, e.ABS_RX, e.ABS_RY):
        ui.write(e.EV_ABS, axis, 0)
    ui.syn()


def simulate_keep_alive(
    ui: UInput,
    count: int,
    interval_seconds: int,
    no_jump: bool = False,
):
    """Sends a discrete gamepad button press (InputBegan/InputEnded) and balanced stick nudge."""
    now = datetime.now()
    x = random.choice([-STICK_DEFLECTION, STICK_DEFLECTION])
    y = random.choice([-STICK_DEFLECTION, STICK_DEFLECTION])
    btn = e.BTN_THUMBL if no_jump else e.BTN_A

    try:
        if no_jump:
            # Camera nudge + discrete L3 click without moving or jumping
            ui.write(e.EV_ABS, e.ABS_RX, x)
            ui.write(e.EV_KEY, btn, 1)
            ui.syn()
            time.sleep(0.22)

            ui.write(e.EV_KEY, btn, 0)
            ui.write(e.EV_ABS, e.ABS_RX, -x)
            ui.syn()
            time.sleep(0.20)
        else:
            # Step + camera nudge + discrete A (Jump) press -> counter-step back
            ui.write(e.EV_ABS, e.ABS_X, x)
            ui.write(e.EV_ABS, e.ABS_Y, y)
            ui.write(e.EV_ABS, e.ABS_RX, -x)
            ui.write(e.EV_KEY, btn, 1)
            ui.syn()
            time.sleep(0.25)

            ui.write(e.EV_KEY, btn, 0)
            ui.write(e.EV_ABS, e.ABS_X, -x)
            ui.write(e.EV_ABS, e.ABS_Y, -y)
            ui.write(e.EV_ABS, e.ABS_RX, x)
            ui.syn()
            time.sleep(0.22)
    finally:
        reset_inputs(ui)

    # Action badge
    if no_jump:
        action_label = "L3 + Camera ↔"
    else:
        dir_name = ("↗ UP-RIGHT" if x > 0 and y < 0 else
                    "↖ UP-LEFT" if x < 0 and y < 0 else
                    "↘ DOWN-RIGHT" if x > 0 else "↙ DOWN-LEFT")
        action_label = f"{dir_name} + Jump"

    time_now = now.strftime('%I:%M %p')
    next_time = (now + timedelta(seconds=interval_seconds)).strftime('%I:%M %p')
    interval_label = format_time(interval_seconds)

    sys.stdout.write(CLEAR)
    render_box(
        f"{YELLOW}☕{RESET}", f"Caffeine Active #{count:03d} [{time_now}]",
        [
            (f"{BLUE}{RESET} ", f"Action: {action_label}"),
            (f"{CYAN}󰅐{RESET} ", f"Next: {next_time} (in {interval_label})"),
        ]
    )


def wait_with_progress(session_start: float, interval_seconds: int):
    """Renders a live single-line animated progress bar with monotonic drift-free timing."""
    deadline = time.monotonic() + interval_seconds

    if not sys.stdout.isatty():
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(remaining)
        return

    tick = 0
    while True:
        now_mono = time.monotonic()
        rem = deadline - now_mono
        if rem <= 0:
            break

        elapsed = interval_seconds - rem
        bar_len = 10
        filled = min(bar_len, max(0, int((elapsed / interval_seconds) * bar_len)))
        bar = '█' * filled + '░' * (bar_len - filled)

        spin = SPINNER[tick % len(SPINNER)]
        rem_m = int((rem + 59) // 60)
        rem_str = f"~{rem_m}m" if rem_m > 1 else "<1m"
        uptime_str = format_time(int(now_mono - session_start))

        sys.stdout.write(
            f"{CLEAR} {CYAN}{spin}{RESET} Next in {rem_str} [{GREEN}{bar}{RESET}] • Uptime: {uptime_str} "
        )
        sys.stdout.flush()
        tick += 1
        time.sleep(min(1.0, max(0.05, deadline - time.monotonic())))

    sys.stdout.write(CLEAR)
    sys.stdout.flush()


def parse_resolution(res: str):
    """Parses a 'WxH' resolution string into (width, height)."""
    parts = res.lower().split("x")
    if len(parts) != 2:
        return None
    try:
        w, h = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if w < 320 or h < 240:
        return None
    return w, h


def launch_sober_gamescope(width: int, height: int, sensitivity: float = None) -> bool:
    """Launches Sober inside gamescope so it keeps focus while running in the background."""
    if os.geteuid() == 0:
        print(f"{RED}✕ Do not run '--launch' with sudo (Flatpak/gamescope must run as your user).{RESET}")
        print(f"  Run {CYAN}roblox-caffeine --setup{RESET} once, then run without sudo.")
        return False

    if not shutil.which("gamescope"):
        render_box(
            f"{RED}✕{RESET}", f"{BOLD}gamescope Not Installed{RESET}",
            [
                (f"{YELLOW}󰋖{RESET} ", "Fedora: sudo dnf install gamescope"),
                (f"{YELLOW}󰋖{RESET} ", "Arch:   sudo pacman -S gamescope"),
                (f"{YELLOW}󰋖{RESET} ", "Ubuntu: sudo apt install gamescope"),
            ]
        )
        print()
        return False

    if not shutil.which("flatpak"):
        print(f"{RED}✕ 'flatpak' is required to launch Sober.{RESET}")
        return False

    sober_check = subprocess.run(
        ["flatpak", "info", "org.vinegarhq.Sober"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if sober_check.returncode != 0:
        print(f"{RED}✕ Sober Flatpak (org.vinegarhq.Sober) is not installed.{RESET}")
        print("  Install it from https://sober.vinegarhq.org/")
        return False

    cmd = [
        "gamescope",
        "--backend", "sdl",
        "-W", str(width), "-H", str(height),
        "-w", str(width), "-h", str(height),
        "-o", str(GAMESCOPE_UNFOCUSED_FPS),
    ]
    if sensitivity is not None:
        cmd.extend(["-s", f"{sensitivity:g}"])
    cmd.extend([
        "--force-grab-cursor",
        "--force-windows-fullscreen",
        "--",
        "flatpak", "run",
        "--nosocket=wayland",
        "--socket=x11",
        "--env=SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS=1",
        "org.vinegarhq.Sober",
    ])
    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except Exception as ex:
        print(f"{RED}✕ Failed to launch Sober in gamescope: {ex}{RESET}")
        return False


def parse_args():
    """Parses CLI options while preserving minimalist usage."""
    parser = argparse.ArgumentParser(
        prog="roblox-caffeine",
        description="Keep your Roblox window awake on Linux via virtual Xbox 360 gamepad pulses.",
        add_help=False,
    )
    parser.add_argument("-s", "--setup", action="store_true", help="Configure /dev/uinput permissions with sudo")
    parser.add_argument(
        "-l", "--launch",
        action="store_true",
        help="Launch Sober inside gamescope alongside roblox-caffeine",
    )
    parser.add_argument(
        "--res",
        type=str,
        default=DEFAULT_GAMESCOPE_RES,
        metavar="WxH",
        help=f"Gamescope resolution for --launch (default: {DEFAULT_GAMESCOPE_RES})",
    )
    parser.add_argument(
        "--sens",
        type=float,
        default=None,
        metavar="MULT",
        help="Gamescope mouse sensitivity multiplier (e.g. 0.6 or 1.5)",
    )
    parser.add_argument(
        "-i", "--interval",
        type=int,
        default=DEFAULT_INTERVAL_MINUTES,
        metavar="MIN",
        help=f"Pulse interval in minutes (1-15, default: {DEFAULT_INTERVAL_MINUTES})",
    )
    parser.add_argument(
        "--no-jump",
        action="store_true",
        help="Use L3 click + camera nudge instead of jumping/walking",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Send a single test pulse immediately and exit",
    )
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.help:
        print_banner()
        print("Usage: roblox-caffeine [OPTIONS]\n")
        print("Options:")
        print("  -l, --launch         Launch Sober inside gamescope + start keep-alive")
        print(f"      --res WxH        Gamescope window resolution (default: {DEFAULT_GAMESCOPE_RES})")
        print("      --sens MULT      Gamescope mouse sensitivity multiplier (e.g. 0.6, 1.5)")
        print(f"  -i, --interval MIN   Pulse interval in minutes (1-15, default: {DEFAULT_INTERVAL_MINUTES})")
        print("      --no-jump        Use L3 click + camera nudge instead of jumping/walking")
        print("      --test           Fire a single test pulse and exit")
        print("  -s, --setup          Configure /dev/uinput permissions with sudo")
        print("  -h, --help           Show this help message and exit\n")
        return

    if args.setup:
        run_setup()
        return

    if not 1 <= args.interval <= 15:
        print(f"{RED}✕ Interval must be between 1 and 15 minutes (Roblox kicks at 20m).{RESET}")
        sys.exit(1)

    if args.sens is not None and not (0.05 <= args.sens <= 10.0):
        print(f"{RED}✕ Sensitivity multiplier must be between 0.05 and 10.0.{RESET}")
        sys.exit(1)

    res_dims = None
    if args.launch:
        res_dims = parse_resolution(args.res)
        if not res_dims:
            print(f"{RED}✕ Invalid resolution '{args.res}'. Use WxH format (e.g., 1920x1080).{RESET}")
            sys.exit(1)

    interval_seconds = args.interval * 60
    mode_label = "Virtual Xbox 360 (No-Jump)" if args.no_jump else "Virtual Xbox 360 Gamepad"

    # Startup Banner & Header
    print_banner()

    try:
        ui = UInput(
            CAPABILITIES,
            name="Microsoft X-Box 360 pad",
            vendor=0x045e,
            product=0x028e,
            version=0x0110
        )
    except PermissionError:
        render_box(
            f"\033[91m✕\033[0m", f"{BOLD}Permission Denied (/dev/uinput){RESET}",
            [
                (f"{YELLOW}󰋖{RESET} ", "Run with '--setup' to configure"),
                (f"{CYAN}💡{RESET} ", "Or run: sudo roblox-caffeine"),
            ]
        )
        return
    except Exception as ex:
        print(f"\033[91m✕ Error creating virtual device: {ex}\033[0m")
        return

    header_rows = [
        (f"{BLUE}{RESET} ", mode_label),
        (f"{CYAN}󰅐{RESET} ", f"Interval: Every {format_time(interval_seconds)}"),
    ]

    if args.launch:
        width, height = res_dims
        if not launch_sober_gamescope(width, height, sensitivity=args.sens):
            ui.close()
            sys.exit(1)
        sens_suffix = f", sens {args.sens:g}x" if args.sens is not None else ""
        header_rows.append(
            (f"{GREEN}󰖲{RESET} ", f"Sober: gamescope ({width}x{height}{sens_suffix})")
        )

    render_box(f"{YELLOW}☕{RESET}", f"{BOLD}Roblox Caffeine{RESET}", header_rows)
    print()

    session_start = time.monotonic()
    pulse_count = 0

    try:
        # Give udev and SDL3/Sober time to detect and open the new virtual gamepad
        time.sleep(DEVICE_WARMUP_SECONDS)

        pulse_count = 1
        simulate_keep_alive(ui, pulse_count, interval_seconds, no_jump=args.no_jump)
        if args.test:
            return
        while True:
            wait_with_progress(session_start, interval_seconds)
            pulse_count += 1
            simulate_keep_alive(ui, pulse_count, interval_seconds, no_jump=args.no_jump)
    except KeyboardInterrupt:
        uptime_str = format_time(int(time.monotonic() - session_start))
        sys.stdout.write(CLEAR)
        render_box(
            f"{YELLOW}☕{RESET}", f"{BOLD}Roblox Caffeine Stopped{RESET}",
            [
                (f"{BLUE}{RESET} ", "Gamepad released"),
                (f"{CYAN}󰅐{RESET} ", f"Session: {uptime_str} ({pulse_count} active events)"),
            ]
        )
        print()
    finally:
        ui.close()

if __name__ == "__main__":
    main()