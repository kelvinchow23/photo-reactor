"""Host-only startup/idle checks for the supported entry points."""
import contextlib
import io
from pathlib import Path
import runpy
import sys
import unittest
from unittest.mock import patch
from sim_hardware import Hardware


class Startup(unittest.TestCase):
    def test_boot_commands_all_channels_idle_without_starting_pwm(self):
        hw = Hardware()
        with patch.dict(sys.modules, {'machine': hw.machine}):
            runpy.run_path(str(Path(__file__).resolve().parents[1] / 'boot.py'))
        for gpio in (0, 1, 4, 5, 8, 9, 12, 13):
            self.assertEqual(hw.pins[gpio], 0)
        for gpio in (2, 3, 6, 7, 10, 11, 14, 15):
            self.assertEqual(hw.pins[gpio], 1)
        self.assertFalse(hw.pwm)

    def test_manual_prompt_never_starts_system_check_or_demo(self):
        for name in ('rev_a_system_check.py', 'rev_a_demo.py'):
            with self.subTest(name=name):
                hw = Hardware()
                with patch.dict(sys.modules, {'machine':hw.machine, 'time':hw.time}):
                    p = runpy.run_path(str(Path(__file__).resolve().parents[1] / name))
                with patch('builtins.input', return_value=''), contextlib.redirect_stdout(io.StringIO()):
                    p['main']()
                self.assertEqual(hw.now, 0)
                self.assertFalse(hw.duties)
                self.assertFalse(hw.pwm)
                self.assertFalse(any(hw.handlers.values()))
                for gpio in p['LED_GPIO']:
                    self.assertEqual(hw.pins[gpio], 0)
                for gpio in p['FAN_GPIO']:
                    self.assertEqual(hw.pins[gpio], 1)
