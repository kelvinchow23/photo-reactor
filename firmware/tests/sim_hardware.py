"""Computer-only simulated Pico GPIO/PWM/tach hardware."""
import types


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
        for fan_gpio, tach_gpio in ((2, 16), (3, 17), (6, 18), (7, 19), (10, 20), (11, 21), (14, 22), (15, 26)):
            pwm = self.pwm.get(fan_gpio)
            duty = (65535 - pwm.duty) / 65535 if pwm else 0
            # 6000RPM * two rising edges/revolution -> 200Hz at full speed.
            edges = round(200 * duty * duration / 1000)
            handler = self.handlers.get(tach_gpio)
            if handler:
                for _ in range(edges):
                    handler(None)
        self.now += duration
