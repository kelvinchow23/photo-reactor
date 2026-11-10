# Rev A bench firmware

These standalone MicroPython programs target the original Raspberry Pi Pico / Pico H
on the SDL4-0001 controller. They do not require the original project's
`photo_reactor.py` or EMC2101 library. Those original files are for different hardware.

| Program | Purpose |
| --- | --- |
| [rev_a_reactor1_test.py](rev_a_reactor1_test.py) | Start here for two fans and two LEDs on REACTOR 1. Reports RPM, tests independent fan commands and gives brief LED flashes. |
| [rev_a_led_check.py](rev_a_led_check.py) | Test all eight LED channels individually with `check(1)` through `check(8)`. |
| [rev_a_bringup.py](rev_a_bringup.py) | Initial controller voltage checks, with reactor cables unplugged. Keeps all LED controls off. |

## Run the reactor 1 test

1. Connect one two-board reactor assembly to REACTOR 1. First board = stir fan;
   second board = cooling fan. Leave the second OUT connector empty.
2. With power disconnected, fit JP_FANV across pins 2-3 for the specified 5V fans.
3. Connect USB, open `rev_a_reactor1_test.py` in Thonny and run it with the Pico
   MicroPython interpreter. It starts with LED controls off and fan commands at 0%.
4. At the prompt, apply the 12V supply, type `TEST` and press Enter.
5. Observe the fan identities and LED reflections. The approximately 52-second
   sequence tests 100%/60% fan commands and two separate one-second LED flashes.

Afterward, `test_fans()` repeats the fan sequence; `check(1)` and `check(2)` test
the two LEDs. `all_off()` commands LEDs off and fan PWM to 0%. Some fans may keep
a minimum speed; disconnect 12V for physical power-off. Ctrl+C performs normal
exception cleanup. A reset, interpreter failure or electrical fault is not covered
by that software cleanup. Disconnect 12V before moving cables.

The LED scripts use a fixed 20% GPIO duty at 1kHz for short bench checks. The fitted
divider/filter converts this to an analog control signal; it is not calibrated
20% light output. This is not continuous-operation firmware. Low-end dimming,
current, control ripple, thermal limits and watchdog behaviour still require work.
Do not look directly into the bare LEDs; observe reflected light.

For standalone boot testing, save the chosen program on the Pico as `main.py`.
Keep only one chosen `main.py`; these are alternatives, not modules to run together.

## Host checks

From the repository root:

```sh
python -m unittest discover -s firmware -p "test_*.py" -v
```

These simulated checks cover GPIO selection, inverted fan duty, two-pulse RPM
calculation, bounded LED tests and exception cleanup. They do not validate hardware.

See [bench results](../docs/bench-results.md) for the physical checks performed so far.
