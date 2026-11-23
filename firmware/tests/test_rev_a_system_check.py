"""Simulated isolation, sequence, RPM and stop checks for the system diagnostic."""
import contextlib
import io
from pathlib import Path
import runpy
import sys
import unittest
from unittest.mock import patch
from sim_hardware import Hardware


class SystemCheck(unittest.TestCase):
    def load(self):
        hw = Hardware()
        with patch.dict(sys.modules, {'machine':hw.machine, 'time':hw.time}):
            p = runpy.run_path(str(Path(__file__).resolve().parents[1].joinpath('rev_a_system_check.py')))
        return hw, p

    def off(self, hw, p):
        self.assertFalse(hw.pwm)
        self.assertFalse(any(hw.handlers.values()))
        for g in p['LED_GPIO']:
            self.assertEqual(hw.pins[g], 0)
        for g in p['FAN_GPIO']:
            self.assertEqual(hw.pins[g], 1)

    def test_three_sequential_full_load_and_cleanup(self):
        hw, p = self.load()
        combined = []
        def wait(ms):
            if ms == 2000:
                combined.append({g:(v.freq, v.duty) for g,v in hw.pwm.items()})
            hw.sleep_ms(ms)
        p['test_3'].__globals__['sleep_ms'] = wait
        with contextlib.redirect_stdout(io.StringIO()):
            p['test_3']()
        self.assertEqual(len(combined), 3)
        for reactor, state in enumerate(combined):
            i = 2 * reactor
            expected = {g:(25000, 0) for g in p['FAN_GPIO'][i:i+2]}
            expected.update({g:(1000, 65535) for g in p['LED_GPIO'][i:i+2]})
            self.assertEqual(state, expected)
        self.assertEqual(hw.now, 17000)
        self.off(hw, p)

    def test_three_together_full_load_and_cleanup(self):
        hw, p = self.load()
        combined = []
        def wait(ms):
            if ms == 2000:
                combined.append({g:(v.freq, v.duty) for g,v in hw.pwm.items()})
            hw.sleep_ms(ms)
        p['test_3_together'].__globals__['sleep_ms'] = wait
        with contextlib.redirect_stdout(io.StringIO()):
            rpm = p['test_3_together']()
        expected = {g:(25000, 0) for g in p['FAN_GPIO'][:6]}
        expected.update({g:(1000, 65535) for g in p['LED_GPIO'][:6]})
        self.assertEqual(combined, [expected])
        self.assertEqual(rpm, [6000]*6)
        self.assertEqual(hw.now, 5000)
        self.off(hw, p)

    def test_three_together_missing_fan_blocks_leds(self):
        hw, p = self.load()
        def wait(ms):
            hw.handlers[21] = None  # Missing R3 cooling feedback.
            hw.sleep_ms(ms)
        p['test_3_together'].__globals__['sleep_ms'] = wait
        with contextlib.redirect_stdout(io.StringIO()):
            rpm = p['test_3_together']()
        self.assertEqual(rpm[-1], 0)
        self.assertFalse(any(g in p['LED_GPIO'] and duty > 0 for g,hz,duty in hw.duties))
        self.off(hw, p)

    def test_three_together_interrupt_cleans_up_combined_load(self):
        hw, p = self.load()
        def wait(ms):
            if ms == 2000:
                raise KeyboardInterrupt()
            hw.sleep_ms(ms)
        p['test_3_together'].__globals__['sleep_ms'] = wait
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(KeyboardInterrupt):
            p['test_3_together']()
        self.off(hw, p)

    def test_complete_sequence_isolates_each_of_sixteen_elements(self):
        hw, p = self.load()
        active_order = []
        def wait(ms):
            self.assertLessEqual(len(hw.pwm), 1)
            if hw.pwm:
                gpio = next(iter(hw.pwm))
                if not active_order or active_order[-1] != gpio:
                    active_order.append(gpio)
                # Every channel other than the selected one retains its off command.
                for g in p['LED_GPIO']:
                    if g != gpio: self.assertEqual(hw.pins[g], 0)
                for g in p['FAN_GPIO']:
                    if g != gpio: self.assertEqual(hw.pins[g], 1)
            hw.sleep_ms(ms)
        p['test_all'].__globals__['sleep_ms'] = wait
        with contextlib.redirect_stdout(io.StringIO()):
            results = p['test_all']()
        expected = []
        for i in range(0, 8, 2):
            expected += [p['FAN_GPIO'][i], p['FAN_GPIO'][i+1], p['LED_GPIO'][i], p['LED_GPIO'][i+1]]
        self.assertEqual(active_order, expected)
        self.assertEqual(hw.now, 84000)
        self.assertEqual(len(results), 4)
        for r in results:
            self.assertEqual(r['stir'][-1], (1800, 0))
            self.assertEqual(r['cool'][-1], (0, 6000))
        self.off(hw, p)

    def test_manual_commands_select_every_channel(self):
        for reactor in range(1,5):
            for kind, args, gpio in (
                ('mix',(reactor,23,1), (2,6,10,14)[reactor-1]),
                ('cool',(reactor,100,1), (3,7,11,15)[reactor-1]),
                ('led',(reactor,1), (0,4,8,12)[reactor-1]),
                ('led',(reactor,2), (1,5,9,13)[reactor-1])):
                hw,p = self.load()
                seen = []
                def wait(ms):
                    seen.append(set(hw.pwm))
                    hw.sleep_ms(ms)
                p[kind].__globals__['sleep_ms'] = wait
                with contextlib.redirect_stdout(io.StringIO()):p[kind](*args)
                self.assertTrue(seen)
                self.assertTrue(all(s == {gpio} for s in seen))
                self.off(hw,p)

    def test_interrupt_fan_and_led_cleanup(self):
        for kind,args in [('mix',(4,30,3)),('cool',(2,100,3)),('led',(3,2))]:
            hw,p = self.load()
            hw.fail_sleep = True
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(KeyboardInterrupt):p[kind](*args)
            self.off(hw,p)

    def test_missing_tach_bounds_hold(self):
        hw,p = self.load()
        def wait(ms): hw.now += ms
        p['mix'].__globals__['sleep_ms'] = wait
        with contextlib.redirect_stdout(io.StringIO()):samples=p['mix'](1,30,60)
        self.assertEqual(samples,[(0,0)]*3)
        self.assertEqual(hw.now,8000)
        self.off(hw,p)

    def test_invalid_requests_do_not_activate(self):
        hw,p = self.load()
        for kind,args in [('mix',(5,30,3)),('cool',(1,101,3)),('led',(1,3)),('led',(1,1,60)),('test_all',(0,))]:
            with self.assertRaises(ValueError):p[kind](*args)
            self.off(hw,p)
