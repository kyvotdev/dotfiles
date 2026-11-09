#!/bin/bash
# Run in your normal terminal; driver installation requires sudo.
set -euo pipefail
if [[ $(cat /sys/bus/pci/devices/0000:03:00.0/vendor) != 0x10de || $(cat /sys/bus/pci/devices/0000:03:00.0/device) != 0x1fb7 ]]; then
    echo 'This installer is prepared for the NVIDIA T550 at 03:00.0.' >&2
    exit 1
fi
sudo pacman -Syu --needed linux-zen-headers nvidia-open-dkms nvidia-utils egl-wayland nvidia-prime
sudo install -d -m 755 /etc/modprobe.d
printf '%s\n' 'options nvidia_drm modeset=1' | sudo tee /etc/modprobe.d/pixel-nvidia.conf >/dev/null
sudo mkinitcpio -P
printf '\n%s\n' 'Installation finished. Save your work and reboot.'
printf '%s\n' 'After reboot: ~/.local/bin/pixel-gpu discrete' 'Then log out of niri and log in again.'
