#!/usr/bin/env python3
"""
Roblox Caffeine - Minimalist Keep-Alive Utility for Linux / Sober
Periodically nudges virtual gamepad thumbsticks via /dev/uinput to prevent idle timeouts.
"""

import argparse
import random
import sys
import time
from datetime import datetime, timedelta

import evdev
from evdev import UInput, ecodes as e

# ==============================================================================
# Minimal Fastfetch Aesthetic Styling
# ==============================================================================
GRAY = '\033[90m'
CYAN = '\033[96m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
BOLD = '\033[1m'
DIM = '\033[2m'
RESET = '\033[0m'
CLEAR = '\r\033[K'
WIDTH = 40

SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
STICK_DEFLECTION = 22000
DEFAULT_INTERVAL_SECONDS = 10 * 60  # 10 minutes

BANNER_ART = r"""
 ___  ___  ___ _    _____  __   ___   _   ___ ___ ___ ___ _  _ ___ 
| _ \/ _ \| _ ) |  / _ \ \/ /  / __| /_\ | __| __| __|_ _| \| | __|
|   / (_) | _ \ |_| (_) >  <  | (__ / _ \| _|| _|| _| | || .` | _| 
|_|_\\___/|___/____\___/_/\_\  \___/_/ \_\_| |_| |___|___|_|\_|___|
"""

# Xbox 360 profile for native SDL2 / Sober compatibility
CAPABILITIES = {
    e.EV_KEY: [
        e.BTN_A, e.BTN_B, e.BTN_X, e.BTN_Y,
        e.BTN_TL, e.BTN_TR, e.BTN_SELECT, e.BTN_START,
        e.BTN_THUMBL, e.BTN_THUMBR,
    ],
    e.EV_ABS: [
        (e.ABS_X, evdev.AbsInfo(0, -32768, 32767, 16, 128, 0)),
        (e.ABS_Y, evdev.AbsInfo(0, -32768, 32767, 16, 128, 0)),
        (e.ABS_RX, evdev.AbsInfo(0, -32768, 32767, 16, 128, 0)),
        (e.ABS_RY, evdev.AbsInfo(0, -32768, 32767, 16, 128, 0)),
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

def simulate_keep_alive(ui: UInput, count: int, interval_sec: int):
    """Nudges left & right thumbsticks and returns them to center."""
    now = datetime.now()
    x = random.choice([-STICK_DEFLECTION, STICK_DEFLECTION])
    y = random.choice([-STICK_DEFLECTION, STICK_DEFLECTION])

    # Nudge movement and camera
    ui.write(e.EV_ABS, e.ABS_X, x)
    ui.write(e.EV_ABS, e.ABS_Y, y)
    ui.write(e.EV_ABS, e.ABS_RX, -x)
    ui.syn()
    time.sleep(0.3)

    # Re-center axes cleanly
    for axis in (e.ABS_X, e.ABS_Y, e.ABS_RX, e.ABS_RY):
        ui.write(e.EV_ABS, axis, 0)
    ui.syn()

    # Direction badge
    dir_name = ("↗ UP-RIGHT" if x > 0 and y < 0 else
                "↖ UP-LEFT" if x < 0 and y < 0 else
                "↘ DOWN-RIGHT" if x > 0 else "↙ DOWN-LEFT")

    time_now = now.strftime('%I:%M %p')
    next_time = (now + timedelta(seconds=interval_sec)).strftime('%I:%M %p')

    sys.stdout.write(CLEAR)
    render_box(
        f"{YELLOW}☕{RESET}", f"Caffeine Active #{count:03d} [{time_now}]",
        [
            (f"{BLUE}{RESET} ", f"Motion: {dir_name}"),
            (f"{CYAN}󰅐{RESET} ", f"Next: {next_time} (in {format_time(interval_sec)})"),
        ]
    )

def wait_with_progress(interval_sec: int, session_start: float):
    """Renders a live single-line animated progress bar during wait interval."""
    if not sys.stdout.isatty():
        time.sleep(interval_sec)
        return

    for tick in range(interval_sec):
        rem = interval_sec - tick
        bar_len = 10
        filled = int((tick / interval_sec) * bar_len)
        bar = '█' * filled + '░' * (bar_len - filled)

        spin = SPINNER[tick % len(SPINNER)]
        rem_m = (rem + 59) // 60
        rem_str = f"~{rem_m}m" if rem_m > 1 else "<1m"
        uptime_str = format_time(int(time.time() - session_start))

        sys.stdout.write(
            f"{CLEAR} {CYAN}{spin}{RESET} Next in {rem_str} [{GREEN}{bar}{RESET}] • Uptime: {uptime_str} "
        )
        sys.stdout.flush()
        time.sleep(1)

    sys.stdout.write(CLEAR)
    sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser(description="Roblox Caffeine - Minimalist Keep-Alive Utility")
    parser.add_argument(
        "-i", "--interval",
        type=int,
        default=DEFAULT_INTERVAL_SECONDS,
        help=f"Pulse interval in seconds (default: {DEFAULT_INTERVAL_SECONDS}s / 10m)"
    )
    args = parser.parse_args()

    # Startup Banner & Header
    print_banner()
    render_box(
        f"{YELLOW}☕{RESET}", f"{BOLD}Roblox Caffeine{RESET}",
        [
            (f"{BLUE}{RESET} ", "Virtual Xbox 360 Gamepad"),
            (f"{CYAN}󰅐{RESET} ", f"Interval: Every {format_time(args.interval)}"),
        ]
    )
    print()

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
                (f"{YELLOW}󰋖{RESET} ", "Run with sudo or add user to 'input' group"),
            ]
        )
        return
    except Exception as ex:
        print(f"\033[91m✕ Error creating virtual device: {ex}\033[0m")
        return

    session_start = time.time()
    pulse_count = 1

    try:
        simulate_keep_alive(ui, pulse_count, args.interval)
        while True:
            wait_with_progress(args.interval, session_start)
            pulse_count += 1
            simulate_keep_alive(ui, pulse_count, args.interval)
    except KeyboardInterrupt:
        uptime_str = format_time(int(time.time() - session_start))
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