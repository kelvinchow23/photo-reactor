"""Standalone MicroPython demo: R1..R3 fan crescendo and green-light show.

Original Pico / PCB Rev A. R4 stays commanded off. Heatsinks must be fitted.
Short indication patterns use 20% GPIO duty; finale uses 100% for two seconds.
No optical/current/temperature sensing. Software off leaves supplies live.
"""
from machine import Pin, PWM, disable_irq, enable_irq
from time import sleep_ms, ticks_ms, ticks_diff

LED_GPIO = (0, 1, 4, 5, 8, 9, 12, 13)
FAN_GPIO = (2, 3, 6, 7, 10, 11, 14, 15)
TACH_GPIO = (16, 17, 18, 19, 20, 21, 22, 26)
_leds = []
_fans = []
_tach_pins = []
_handlers = []
_counts = [0] * 6


def all_off():
    """Command every channel off; does not disconnect electrical power."""
    while _leds:
        output = _leds.pop()
        try:
            output.duty_u16(0)
        finally:
            output.deinit()
    while _fans:
        output = _fans.pop()
        try:
            output.duty_u16(65535)
        finally:
            output.deinit()
    for pin in _tach_pins:
        pin.irq(handler=None)
    _tach_pins[:] = []
    _handlers[:] = []
    for gpio in LED_GPIO:
        Pin(gpio, Pin.OUT, value=0)
    for gpio in FAN_GPIO:
        Pin(gpio, Pin.OUT, value=1)


all_off()


def _handler(index):
    def count(pin):
        _counts[index] += 1
    return count


def _snapshot():
    state = disable_irq()
    try:
        return ticks_ms(), _counts[:]
    finally:
        enable_irq(state)


def _feedback():
    start, before = _snapshot()
    sleep_ms(1000)
    end, after = _snapshot()
    elapsed = ticks_diff(end, start)
    if elapsed <= 0:
        raise RuntimeError('Invalid tach measurement interval')
    rpm = [(b-a)*60000/(2*elapsed) for a,b in zip(before, after)]
    for reactor in (1, 2, 3):
        i = 2*(reactor-1)
        print('R%d: STIR %.0f RPM / COOL %.0f RPM' % (reactor, rpm[i], rpm[i+1]))
    if any(speed == 0 for speed in rpm):
        raise RuntimeError('Missing fan feedback; demo stopped. Check fans and supply.')
    return rpm


def _lights(indices=(), duty=13107):
    for index, output in enumerate(_leds):
        output.duty_u16(duty if index in indices else 0)


def demo():
    """One ~23-second show; Ctrl+C stops. No automatic repetition."""
    all_off()
    try:
        for index, gpio in enumerate(TACH_GPIO[:6]):
            _counts[index] = 0
            pin = Pin(gpio, Pin.IN)
            _tach_pins.append(pin)
            handler = _handler(index)
            _handlers.append(handler)
            pin.irq(trigger=Pin.IRQ_RISING, handler=handler)
        for gpio in FAN_GPIO[:6]:
            _fans.append(PWM(Pin(gpio), freq=25000, duty_u16=65535))
        for gpio in LED_GPIO[:6]:
            _leds.append(PWM(Pin(gpio), freq=1000, duty_u16=0))

        print('\nACT 1: THE FAN ORCHESTRA')
        # Add stirring fans across R1..R3, then cooling fans across R1..R3.
        for index in (0, 2, 4, 1, 3, 5):
            print('Adding R%d %s; earlier fans stay on.' %
                  (index//2+1, ('STIR', 'COOL')[index%2]))
            for step in range(1, 21):
                _fans[index].duty_u16(round(65535*(20-step)/20))
                sleep_ms(50)
            sleep_ms(500)
        print('Six fans playing. Checking RPM before the light show:')
        _feedback()

        print('\nACT 2: REACTOR RUNWAY (20% GPIO duty)')
        for direction in ((0, 1, 2), (2, 1, 0)):
            for reactor in direction:
                _lights((2*reactor, 2*reactor+1))
                sleep_ms(350)
                _lights()
                sleep_ms(150)

        print('\nACT 3: LEFT, RIGHT, LEFT, RIGHT')
        for _ in range(2):
            _lights((0, 2, 4))
            sleep_ms(350)
            _lights((1, 3, 5))
            sleep_ms(350)
        _lights()
        sleep_ms(500)

        print('\nACT 4: THREE REACTORS, ONE BEAT')
        for _ in range(3):
            _lights((0, 1, 2, 3, 4, 5))
            sleep_ms(300)
            _lights()
            sleep_ms(500)

        print('\nFINALE: ALL THREE, FULL COMMAND, TWO SECONDS')
        _lights((0, 1, 2, 3, 4, 5), 65535)
        sleep_ms(2000)
        _lights()
        print('Lights out; fans take their bow:')
        _feedback()
        sleep_ms(2000)
    finally:
        all_off()
        print('Curtain down. All commands OFF; supplies remain live.')


def main():
    try:
        all_off()
        print('\nSDL4 -- THREE-REACTOR DEMO (R1, R2, R3; R4 OFF)')
        print('Heatsinks fitted; magnet carriers contained; observe reflected light.')
        print('Establish idle over USB, then connect external 5V and 12V.')
        print('Modified external-5V board: NO fan-selector jumper.')
        if input('Type DEMO to start, or Enter for manual mode: ').strip().upper() == 'DEMO':
            demo()
    except KeyboardInterrupt:
        print('\nDemo interrupted.')
    finally:
        all_off()
    print('Again: demo(). Stop: Ctrl+C. Off: all_off().')
    print('Disconnect 12V, external 5V and USB before touching any wiring.')


if __name__ == '__main__':
    main()
