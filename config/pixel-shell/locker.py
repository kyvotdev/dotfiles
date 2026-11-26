#!/usr/bin/env python3
"""Supervise the locker independently of idle detection; report real readiness."""
import os
from pathlib import Path
import shutil
import subprocess
from compositor import hyprland


def ready():
    subprocess.run(['systemd-notify', '--ready', '--status=Session locked'], check=True)


def swaylock(log, on_locked=None):
    on_locked = on_locked or ready
    reader, writer = os.pipe()
    proc = subprocess.Popen(['swaylock', '-R', str(writer)],
                            pass_fds=(writer,), stdout=log, stderr=log)
    os.close(writer)
    with os.fdopen(reader, 'rb') as status:
        if status.read(1):
            on_locked()
    return proc.wait()


def lock_screen(on_locked):
    home = Path.home()
    state = home / '.local/state/pixel-shell'
    state.mkdir(parents=True, exist_ok=True)
    with open(state / 'lock.log', 'w') as log:
        # All entry points (idle, lid/sleep, hotkey) share this supervisor.
        # Start password entry in US even when the desktop was using Russian.
        if hyprland():
            try:
                subprocess.run(['hyprctl', 'switchxkblayout', 'all', '0'],
                               stdout=log, stderr=log, timeout=2, check=False)
            except (OSError, subprocess.TimeoutExpired) as error:
                # Layout failures must never prevent the session from locking.
                log.write(f'Could not reset lock keyboard layout: {error}\n')
        if not shutil.which('hyprlock'):
            return swaylock(log, on_locked)
        wallpaper = state / 'wallpaper'
        if wallpaper.exists():
            target = Path(wallpaper.read_text().strip())
            if target.is_file():
                link = state / 'lock-wallpaper'
                temp = state / 'lock-wallpaper.new'
                temp.unlink(missing_ok=True)
                temp.symlink_to(target)
                temp.replace(link)
        try:
            lock_config = home / '.config/blackout-lock/hyprlock.conf'
            config_text = lock_config.read_text()
            if hyprland():
                generated = state / 'hyprlock-orbit.conf'
                generated.write_text(config_text.replace('font_family = Terminess Nerd Font Mono',
                                                         'font_family = JetBrains Mono'))
                lock_config = generated
            proc = subprocess.Popen(
                ['hyprlock', '--no-fade-in', '--config', str(lock_config)],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                env={**os.environ, 'NO_COLOR': '1', 'LC_ALL': 'C'})
        except OSError as error:
            log.write(f'Could not start Hyprlock: {error}; falling back to swaylock.\n')
            log.flush()
            return swaylock(log, on_locked)
        notified = False
        for line in proc.stdout:
            log.write(line)
            log.flush()
            # Hyprlock logs this only in the ext-session-lock-v1 locked callback.
            if not notified and 'onLockLocked called' in line:
                on_locked()
                notified = True
        result = proc.wait()
        if not notified:
            log.write("Hyprlock did not acquire the lock; falling back to swaylock.\n")
            log.flush()
            return swaylock(log, on_locked)
        return result


class LockWifi:
    def __init__(self):
        self.was_enabled = self.command('radio', 'wifi') == 'enabled'
        self.disabled = False

    @staticmethod
    def command(*args):
        try:
            result = subprocess.run(['nmcli', *args], capture_output=True, text=True,
                                    timeout=10, env={**os.environ, 'LC_ALL': 'C'})
            return result.stdout.strip() if result.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None

    def locked(self):
        if self.was_enabled:
            self.disabled = True
            self.command('radio', 'wifi', 'off')

    def unlocked(self):
        if self.disabled:
            self.command('radio', 'wifi', 'on')
            # Explicit disconnect can inhibit NM device autoconnection. Re-enable
            # it on wireless devices so saved profiles reconnect after wake.
            devices = self.command('-t', '-f', 'DEVICE,TYPE', 'device') or ''
            for row in devices.splitlines():
                dev, _, kind = row.rpartition(':')
                if kind == 'wifi':
                    self.command('device', 'set', dev, 'autoconnect', 'yes')


def main():
    wifi = LockWifi()
    def on_locked():
        ready()
        wifi.locked()
    result = lock_screen(on_locked)
    if result == 0:
        wifi.unlocked()
    return result


if __name__ == '__main__':
    raise SystemExit(main())
