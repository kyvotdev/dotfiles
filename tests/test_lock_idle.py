import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import dbus

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pixel_idle', ROOT/'config/pixel-shell/idle.py')
idle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(idle)


class MediaIdleTests(unittest.TestCase):
    def bus(self, statuses):
        bus = Mock()
        bus.list_names.return_value = ['org.example.Other'] + list(statuses)
        def player(name, *args, **kwargs):
            obj = Mock()
            value = statuses[name]
            if isinstance(value, Exception):
                obj.Get.side_effect = value
            else:
                obj.Get.return_value = value
            return obj
        bus.get_object.side_effect = player
        return bus

    def test_video_playing_inhibits(self):
        self.assertTrue(idle.media_playing(self.bus({'org.mpris.MediaPlayer2.firefox': 'Playing'})))

    def test_paused_and_stopped_do_not_inhibit(self):
        self.assertFalse(idle.media_playing(self.bus({
            'org.mpris.MediaPlayer2.firefox': 'Paused',
            'org.mpris.MediaPlayer2.mpv': 'Stopped'})))

    def test_disappearing_player_does_not_hide_another_player(self):
        self.assertTrue(idle.media_playing(self.bus({
            'org.mpris.MediaPlayer2.mpv': dbus.DBusException('gone'),
            'org.mpris.MediaPlayer2.firefox': 'Playing'})))

    def test_stop_waits_for_dpms_resume(self):
        proc = Mock()
        proc.poll.return_value = None
        idle.stop_idle(proc)
        proc.terminate.assert_called_once()
        proc.wait.assert_called_once_with(timeout=10)

    def test_pause_play_pause_restarts_idle_and_stops_on_shutdown(self):
        callbacks = {}
        proc1, proc2 = Mock(), Mock()
        proc1.poll.return_value = proc2.poll.return_value = None
        ticks = 0
        def tick(_):
            nonlocal ticks
            ticks += 1
            if ticks == 3:
                callbacks[idle.signal.SIGTERM]()
        with patch.object(idle.signal, 'signal', side_effect=lambda sig, cb: callbacks.update({sig: cb})), \
             patch.object(idle.dbus, 'SessionBus'), \
             patch.object(idle, 'media_playing', side_effect=[False, True, False]), \
             patch.object(idle, 'start_idle', side_effect=[proc1, proc2]) as start, \
             patch.object(idle.time, 'sleep', side_effect=tick):
            idle.main()
        self.assertEqual(start.call_count, 2)
        proc1.terminate.assert_called_once()
        proc2.terminate.assert_called_once()


spec = importlib.util.spec_from_file_location('pixel_locker', ROOT/'config/pixel-shell/locker.py')
locker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(locker)


class LockerTests(unittest.TestCase):
    def test_hyprland_resets_layout_before_fallback_locker(self):
        with tempfile.TemporaryDirectory() as temp, \
             patch.object(locker.Path, 'home', return_value=Path(temp)), \
             patch.object(locker, 'hyprland', return_value=True), \
             patch.object(locker.shutil, 'which', return_value=None), \
             patch.object(locker.subprocess, 'run') as reset, \
             patch.object(locker, 'swaylock') as fallback:
            fallback.side_effect = lambda *args: self.assertTrue(reset.called) or 0
            self.assertEqual(locker.lock_screen(Mock()), 0)
        self.assertEqual(reset.call_args.args[0], ['hyprctl', 'switchxkblayout', 'all', '0'])

    def test_layout_failure_never_prevents_locking(self):
        with tempfile.TemporaryDirectory() as temp, \
             patch.object(locker.Path, 'home', return_value=Path(temp)), \
             patch.object(locker, 'hyprland', return_value=True), \
             patch.object(locker.shutil, 'which', return_value=None), \
             patch.object(locker.subprocess, 'run', side_effect=OSError('unavailable')), \
             patch.object(locker, 'swaylock', return_value=0) as fallback:
            self.assertEqual(locker.lock_screen(Mock()), 0)
            fallback.assert_called_once()

    def run_locker(self, lines, result):
        proc = Mock()
        proc.stdout = iter(lines)
        proc.wait.return_value = result
        with tempfile.TemporaryDirectory() as temp, \
             patch.object(locker.Path, 'home', return_value=Path(temp)), \
             patch.object(locker, 'hyprland', return_value=False), \
             patch.object(locker.shutil, 'which', return_value='/usr/bin/hyprlock'), \
             patch.object(locker.subprocess, 'Popen', return_value=proc), \
             patch.object(locker, 'LockWifi'), \
             patch.object(locker, 'ready') as ready, \
             patch.object(locker, 'swaylock', return_value=0) as fallback:
            config = Path(temp) / '.config/blackout-lock/hyprlock.conf'
            config.parent.mkdir(parents=True)
            config.write_text('general {}\n')
            actual = locker.main()
        return actual, ready.call_count, fallback.call_count

    def test_compositor_confirmation_notifies_once(self):
        self.assertEqual(self.run_locker([
            'Locking session\n', 'onLockLocked called\n',
            'onLockLocked called\n'], 0), (0, 1, 0))

    def test_startup_failure_falls_back_without_false_readiness(self):
        self.assertEqual(self.run_locker(['Config threw\n'], 1), (0, 0, 1))

    def test_exit_without_lock_confirmation_falls_back(self):
        self.assertEqual(self.run_locker(['Locking session\n'], 0), (0, 0, 1))

    def test_missing_config_falls_back_on_both_compositors(self):
        for is_hyprland in (True, False):
            with self.subTest(hyprland=is_hyprland), \
                 tempfile.TemporaryDirectory() as temp, \
                 patch.object(locker.Path, 'home', return_value=Path(temp)), \
                 patch.object(locker, 'hyprland', return_value=is_hyprland), \
                 patch.object(locker.shutil, 'which', return_value='/usr/bin/hyprlock'), \
                 patch.object(locker.subprocess, 'run'), \
                 patch.object(locker.subprocess, 'Popen') as start, \
                 patch.object(locker, 'swaylock', return_value=0) as fallback:
                callback = Mock()
                self.assertEqual(locker.lock_screen(callback), 0)
                start.assert_not_called()
                fallback.assert_called_once_with(unittest.mock.ANY, callback)
                callback.assert_not_called()



class LockWifiTests(unittest.TestCase):
    def test_enabled_wifi_is_disabled_then_restored_with_autoconnect(self):
        with patch.object(locker.LockWifi, 'command', side_effect=[
                'enabled', '', '', 'wlan0:wifi\neth0:ethernet', '']) as command:
            wifi = locker.LockWifi()
            wifi.locked()
            wifi.unlocked()
        self.assertEqual(command.call_args_list, [
            unittest.mock.call('radio', 'wifi'),
            unittest.mock.call('radio', 'wifi', 'off'),
            unittest.mock.call('radio', 'wifi', 'on'),
            unittest.mock.call('-t', '-f', 'DEVICE,TYPE', 'device'),
            unittest.mock.call('device', 'set', 'wlan0', 'autoconnect', 'yes')])

    def test_manual_radio_off_stays_off(self):
        with patch.object(locker.LockWifi, 'command', return_value='disabled') as command:
            wifi = locker.LockWifi()
            wifi.locked()
            wifi.unlocked()
        command.assert_called_once_with('radio', 'wifi')

    def test_failed_locker_does_not_restore_wifi(self):
        with patch.object(locker, 'LockWifi') as wifi, \
             patch.object(locker, 'lock_screen', return_value=1):
            self.assertEqual(locker.main(), 1)
        wifi.return_value.unlocked.assert_not_called()


if __name__ == '__main__':
    unittest.main()
