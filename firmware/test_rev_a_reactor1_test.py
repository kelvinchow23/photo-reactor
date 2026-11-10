"""Host-side checks of the bounded test sequence; no physical hardware exercised."""
import contextlib
import io
from pathlib import Path
import runpy
import sys
import types
import unittest
from unittest.mock import patch


class Hardware:
    def __init__(self):
        self.now = 0
        self.pins = {}
        self.pwm = {}
        self.handlers = {}
        self.duties = []
        self.fail_sleep = False
        self.max_leds_on = 0
        hardware = self

        class Pin:
            OUT = 1
            IN = 0
            IRQ_RISING = 1

            def __init__(self, gpio, mode=None, value=None):
                self.gpio = gpio
                if value is not None:
                    hardware.pins[gpio] = value

            def irq(self, handler=None, **kwargs):
                hardware.handlers[self.gpio] = handler

        class PWM:
            def __init__(self, pin, freq, duty_u16):
                self.gpio = pin.gpio
                self.freq = freq
                self.duty = duty_u16
                hardware.pwm[self.gpio] = self

            def duty_u16(self, value):
                assert 0 <= value <= 65535
                self.duty = value
                hardware.duties.append((self.gpio, self.freq, value))
                active = sum(p.duty > 0 for g, p in hardware.pwm.items() if g in (0, 1))
                hardware.max_leds_on = max(active, hardware.max_leds_on)

            def deinit(self):
                hardware.pwm.pop(self.gpio, None)

        self.Pin = Pin
        self.machine = types.SimpleNamespace(Pin=Pin, PWM=PWM,
                                             disable_irq=lambda: 0, enable_irq=lambda state: None)
        self.time = types.SimpleNamespace(sleep_ms=self.sleep_ms,
                                          ticks_ms=lambda: self.now,
                                          ticks_diff=lambda a, b: a - b)

    def sleep_ms(self, duration):
        if self.fail_sleep:
            raise KeyboardInterrupt()
        for fan_gpio, tach_gpio in ((2, 16), (3, 17)):
            pwm = self.pwm.get(fan_gpio)
            duty = (65535 - pwm.duty) / 65535 if pwm else 0
            # 6000RPM * two rising edges/revolution -> 200Hz at full speed.
            edges = round(200 * duty * duration / 1000)
            handler = self.handlers.get(tach_gpio)
            if handler:
                for _ in range(edges):
                    handler(None)
        self.now += duration


class TestReactor1(unittest.TestCase):
    def setUp(self):
        self.hardware = Hardware()
        modules = {'machine': self.hardware.machine, 'time': self.hardware.time,
                   'micropython': types.SimpleNamespace(alloc_emergency_exception_buf=lambda n: None)}
        self.patch = patch.dict(sys.modules, modules)
        self.patch.start()
        self.output = io.StringIO()
        self.capture = contextlib.redirect_stdout(self.output)
        self.capture.__enter__()
        self.program = runpy.run_path(str(Path(__file__).with_name('rev_a_reactor1_test.py')))

    def tearDown(self):
        self.capture.__exit__(None, None, None)
        self.patch.stop()

    def assert_off(self):
        self.assertFalse(self.hardware.pwm)
        for gpio in self.program['LED_GPIO']:
            self.assertEqual(self.hardware.pins[gpio], 0)
        for gpio in self.program['FAN_GPIO']:
            self.assertEqual(self.hardware.pins[gpio], 1)

    def test_startup_does_not_energize_outputs(self):
        self.assert_off()
        self.assertFalse(self.hardware.duties)

    def test_fan_inversion_rpm_and_independence(self):
        results = self.program['test_fans']()
        expected = ((6000, 0), (3600, 0), (0, 6000), (0, 3600), (6000, 6000), (3600, 3600))
        self.assertEqual(tuple(row[3] for row in results), expected)
        self.assertEqual(self.hardware.now, 30000)
        self.assertTrue(all(g in (2, 3) and hz == 25000 for g, hz, _ in self.hardware.duties))
        self.assertTrue(all(h is None for h in self.hardware.handlers.values()))
        self.assert_off()

    def test_full_sequence_and_led_limits(self):
        self.program['run_test']()
        self.assertEqual(self.hardware.now, 52000)
        self.assertEqual(self.hardware.max_leds_on, 1)
        positive = [(g, hz, duty) for g, hz, duty in self.hardware.duties if g in (0, 1) and duty > 0]
        self.assertEqual(positive, [(0, 1000, 13107), (1, 1000, 13107)])
        self.assert_off()

    def test_invalid_channels_have_no_output(self):
        for value in (0, 3, 1.0, True, '1'):
            with self.assertRaises(ValueError):
                self.program['check'](value)
        self.assertFalse(self.hardware.duties)

    def test_interrupt_cleanup_for_fans_and_leds(self):
        self.hardware.fail_sleep = True
        for function, args in ((self.program['test_fans'], ()), (self.program['check'], (1,))):
            with self.assertRaises(KeyboardInterrupt):
                function(*args)
            self.assert_off()
        self.assertTrue(all(h is None for h in self.hardware.handlers.values()))

    def test_cancelled_prompt_keeps_outputs_off(self):
        with patch('builtins.input', return_value=''):
            self.program['main']()
        self.assertEqual(self.hardware.now, 0)
        self.assert_off()

    def test_no_tach_is_reported_as_check(self):
        self.hardware.sleep_ms = lambda ms: setattr(self.hardware, 'now', self.hardware.now + ms)
        self.program['test_fans'].__globals__['sleep_ms'] = self.hardware.sleep_ms
        results = self.program['test_fans']()
        self.assertTrue(all(row[3] == (0, 0) for row in results))
        self.assertIn('CHECK -- missing RPM feedback', self.output.getvalue())
        self.assert_off()


if __name__ == '__main__':
    unittest.main()
