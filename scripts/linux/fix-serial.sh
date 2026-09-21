#!/usr/bin/env bash
# fix-serial.sh — make USB serial radios (Meshtastic / MeshCore) usable on Linux.
#
# Debian/Kali/Ubuntu ship brltty and ModemManager, which grab USB serial
# adapters (CH340 / CP210x / FTDI). The radio then shows up in a port scan but
# cannot be opened. This script stops/masks those services and adds your user
# to the dialout group.
#
# Usage:  sudo bash scripts/linux/fix-serial.sh
set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "This script is for Linux only."
    exit 0
fi

if [[ $EUID -ne 0 ]]; then
    echo "Please run with sudo: sudo bash $0"
    exit 1
fi

echo "==> Stopping services that grab USB serial adapters"
for svc in brltty-udev.service brltty.service ModemManager; do
    if systemctl list-unit-files "$svc" >/dev/null 2>&1; then
        systemctl stop "$svc" 2>/dev/null || true
        systemctl mask "$svc" 2>/dev/null || true
        echo "    stopped + masked $svc"
    fi
done

echo "==> Reloading udev rules"
udevadm control --reload-rules 2>/dev/null || true
udevadm trigger 2>/dev/null || true

TARGET_USER="${SUDO_USER:-}"
if [[ -n "$TARGET_USER" ]]; then
    echo "==> Adding $TARGET_USER to the dialout group"
    usermod -aG dialout "$TARGET_USER" || true
fi

echo
echo "Done. Log out and back in (or reboot) for the group change to apply,"
echo "then re-scan ports in Mesh Master and try connecting again."
echo
echo "If a specific device is still locked, unplug it, wait 5 seconds, replug it."
