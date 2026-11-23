"""Host simulation of the bounded demo; not for uploading to Pico."""
import contextlib
import io
from pathlib import Path
import runpy
import sys
import unittest
from unittest.mock import patch
from sim_hardware import Hardware


class Demo(unittest.TestCase):
    def load(self):
        hw = Hardware()
        with patch.dict(sys.modules, {'machine': hw.machine, 'time': hw.time}):
            p = runpy.run_path(str(Path(__file__).resolve().parents[1].joinpath('rev_a_demo.py')))
        return hw, p

    def off(self, hw, p):
        self.assertFalse(hw.pwm)
        self.assertFalse(any(hw.handlers.values()))
        for gpio in p['LED_GPIO']:
            self.assertEqual(hw.pins[gpio], 0)
        for gpio in p['FAN_GPIO']:
            self.assertEqual(hw.pins[gpio], 1)

    def test_crescendo_patterns_finale_and_r4_isolation(self):
        hw, p = self.load()
        stages = []
        def wait(ms):
            fans = {g for g,v in hw.pwm.items() if g in p['FAN_GPIO'] and v.duty == 0}
            leds = {g:v.duty for g,v in hw.pwm.items() if g in p['LED_GPIO'] and v.duty > 0}
            self.assertFalse(set(hw.pwm) & set(p['LED_GPIO'][6:] + p['FAN_GPIO'][6:]))
            stages.append((ms, fans, leds))
            hw.sleep_ms(ms)
        p['demo'].__globals__['sleep_ms'] = wait
        with contextlib.redirect_stdout(io.StringIO()) as output:
            p['demo']()
        additions = [fans for ms,fans,leds in stages if ms == 500 and not leds][:6]
        order = (2, 6, 10, 3, 7, 11)
        self.assertEqual(additions, [set(order[:i]) for i in range(1,7)])
        full = [(ms,fans,leds) for ms,fans,leds in stages if any(v == 65535 for v in leds.values())]
        self.assertEqual(full, [(2000, set(p['FAN_GPIO'][:6]), dict.fromkeys(p['LED_GPIO'][:6],65535))])
        lit = [set(leds) for ms,fans,leds in stages if ms == 350]
        self.assertEqual(lit[:6], [{0,1},{4,5},{8,9},{8,9},{4,5},{0,1}])
        self.assertEqual(lit[6:], [{0,4,8},{1,5,9},{0,4,8},{1,5,9}])
        self.assertEqual(hw.now, 22300)
        self.assertIn('R3: STIR 6000 RPM / COOL 6000 RPM', output.getvalue())
        self.off(hw,p)

    def test_missing_fan_prevents_light_show(self):
        hw,p = self.load()
        def wait(ms):
            hw.handlers[21] = None
            hw.sleep_ms(ms)
        p['demo'].__globals__['sleep_ms'] = wait
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
            p['demo']()
        self.assertFalse(any(g in p['LED_GPIO'] and duty > 0 for g,hz,duty in hw.duties))
        self.off(hw,p)

    def test_interrupt_at_fan_light_and_finale_stages(self):
        for target in (50,350,2000):
            hw,p = self.load()
            def wait(ms):
                if ms == target:
                    raise KeyboardInterrupt()
                hw.sleep_ms(ms)
            p['demo'].__globals__['sleep_ms'] = wait
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(KeyboardInterrupt):
                p['demo']()
            self.off(hw,p)


if __name__ == '__main__':
    unittest.main()
