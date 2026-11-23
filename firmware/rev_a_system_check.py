"""Standalone Thonny functional check, SDL4-0001/0002 PCB Rev A.

Four reactors; each has STIR, COOL, LED A and LED B. Includes individual and combined tests.
Five-second stirring ramp, two-second cooling ramp, live tach feedback.
led() uses 20% duty; test_3()/test_3_together() include bounded full-command LED checks.
All commands start idle and end idle, including Ctrl+C cleanup. Supplies stay live.
"""
from machine import Pin, PWM, disable_irq, enable_irq
from time import sleep_ms, ticks_ms, ticks_diff

LED_GPIO = (0, 1, 4, 5, 8, 9, 12, 13)
FAN_GPIO = (2, 3, 6, 7, 10, 11, 14, 15)
_outputs = []
_led_outputs = []

TACH_GPIO = (16, 17, 18, 19, 20, 21, 22, 26)
TACH_PULSES_PER_REV = 2
_tach_counts = [0, 0]
_tach_pins = []


def _tach_stir(pin):
    _tach_counts[0] += 1


def _tach_cool(pin):
    _tach_counts[1] += 1


def _detach_tach():
    for pin in _tach_pins:
        pin.irq(handler=None)
    _tach_pins[:] = []


def _start_tach(reactor):
    _detach_tach()
    _tach_counts[0] = 0
    _tach_counts[1] = 0
    start = (reactor - 1) * 2
    for gpio, handler in zip(TACH_GPIO[start:start + 2], (_tach_stir, _tach_cool)):
        pin = Pin(gpio, Pin.IN)  # Controller has external 3.3V pull-ups.
        _tach_pins.append(pin)
        pin.irq(trigger=Pin.IRQ_RISING, handler=handler)


def _snapshot():
    state = disable_irq()
    try:
        return ticks_ms(), _tach_counts[0], _tach_counts[1]
    finally:
        enable_irq(state)


def _measure_rpm(duration_ms):
    start, a0, b0 = _snapshot()
    sleep_ms(duration_ms)
    end, a1, b1 = _snapshot()
    elapsed = ticks_diff(end, start)
    if elapsed <= 0:
        raise RuntimeError('Invalid tach measurement interval')
    scale = 60000 / (TACH_PULSES_PER_REV * elapsed)
    return ((a1 - a0) * scale, (b1 - b0) * scale)


def _report_rpm(reactor, rpm):
    print('R%d measured: STIR %.0f RPM / COOL %.0f RPM (stage average, includes startup).' %
          (reactor, rpm[0], rpm[1]))
    for label, speed in zip(('STIR', 'COOL'), rpm):
        if speed == 0:
            print('CHECK R%d %s: no tach pulses; may be stalled or tach wiring is missing.' %
                  (reactor, label))
    print('Tach feedback indicates fan rotation; it does not prove stir-bar coupling.')




def all_off():
    """Stop commands; supply stays live and fans may coast."""
    while _led_outputs:
        output = _led_outputs.pop()
        try:
            output.duty_u16(0)
        finally:
            output.deinit()
    while _outputs:
        output = _outputs.pop()
        try:
            output.duty_u16(65535)
        finally:
            output.deinit()
    _detach_tach()
    for gpio in LED_GPIO:
        Pin(gpio, Pin.OUT, value=0)
    for gpio in FAN_GPIO:
        Pin(gpio, Pin.OUT, value=1)


all_off()



def _reactor(reactor):
    if type(reactor) is not int or reactor not in (1, 2, 3, 4):
        raise ValueError('reactor must be 1..4')
    return 2 * (reactor - 1)


def _fan(reactor, channel, percent, seconds, ramp_seconds):
    start = _reactor(reactor)
    if not isinstance(percent, (int, float)) or not 0 <= percent <= 100:
        raise ValueError('percent must be 0..100')
    if type(seconds) is not int or not 1 <= seconds <= 60:
        raise ValueError('seconds must be a whole number, 1..60')
    if type(ramp_seconds) is not int or not 1 <= ramp_seconds <= 10:
        raise ValueError('ramp_seconds must be a whole number, 1..10')
    label = ('STIR', 'COOL')[channel]
    all_off()
    if percent == 0:
        return []
    samples = []
    no_pulses = 0
    try:
        _start_tach(reactor)
        output = PWM(Pin(FAN_GPIO[start + channel]), freq=25000, duty_u16=65535)
        _outputs.append(output)
        print('R%d %s only: ramp %ds -> %s%%; hold %ds. LEDs OFF.' %
              (reactor, label, ramp_seconds, percent, seconds))
        steps = 20 * ramp_seconds
        for step in range(1, steps + 1):
            command = percent * step / steps
            output.duty_u16(round(65535 * (100-command) / 100))
            sleep_ms(50)
        for second in range(seconds):
            rpm = _measure_rpm(1000)
            samples.append(rpm)
            print('  %d/%ds: STIR %.0f RPM / COOL %.0f RPM' %
                  (second+1, seconds, rpm[0], rpm[1]))
            no_pulses = no_pulses + 1 if rpm[channel] == 0 else 0
            if no_pulses:
                print('  CHECK: active fan has no tach pulses (%d/3).' % no_pulses)
            if no_pulses >= 3:
                print('  Stopping: 3 consecutive seconds without active-fan feedback.')
                break
        if any(sample[channel] > 0 for sample in samples):
            print('  FEEDBACK PRESENT: confirm the correct fan moves and stir bar follows.')
        else:
            print('  NO FEEDBACK: fan may be stalled, stopped, or tach wiring disconnected.')
        if any(sample[1-channel] > 0 for sample in samples):
            print('  NOTE: uncommanded fan reports rotation; check coasting or channel identity.')
    finally:
        all_off()
    return samples


def mix(reactor=1, percent=30, seconds=10, ramp_seconds=5):
    """Stirring fan only; five-second ramp by default. Returns STIR/COOL RPM pairs."""
    return _fan(reactor, 0, percent, seconds, ramp_seconds)


def cool(reactor=1, percent=100, seconds=10, ramp_seconds=2):
    """Cooling fan only; two-second ramp to full speed by default."""
    return _fan(reactor, 1, percent, seconds, ramp_seconds)


def led(reactor=1, channel=1, seconds=1):
    """Brief indication check: LED 1=A/first board, LED 2=B/second board.

Only the selected LED runs, at fixed 20% GPIO duty, for 1..2 whole seconds.
Cooling fans stay off to keep element identification independent. Heatsinks must
be fitted. No light/current feedback is present; identity must be checked visually.
"""
    start = _reactor(reactor)
    if type(channel) is not int or channel not in (1, 2):
        raise ValueError('LED channel must be 1 (A) or 2 (B)')
    if type(seconds) is not int or seconds not in (1, 2):
        raise ValueError('LED indication duration must be 1 or 2 seconds')
    all_off()
    try:
        output = PWM(Pin(LED_GPIO[start+channel-1]), freq=1000, duty_u16=0)
        _led_outputs.append(output)
        print('R%d LED %s only: 20%% GPIO bench duty, %ds. Observe reflected light.' %
              (reactor, ('A','B')[channel-1], seconds))
        output.duty_u16(13107)
        sleep_ms(seconds*1000)
    finally:
        all_off()
    print('  LED OFF. No optical feedback: confirm the intended LED flashed.')


def test_3():
    """R1..R3: ramp both fans, then both LEDs/fans at full command for 2s.

Requires fitted heatsinks and verified fan supply. Full command is not calibrated
optical output. R4 stays commanded off. This is a short functional check only.
"""
    all_off()
    try:
        for reactor in (1, 2, 3):
            all_off()
            start = _reactor(reactor)
            _start_tach(reactor)
            fans = []
            for gpio in FAN_GPIO[start:start + 2]:
                output = PWM(Pin(gpio), freq=25000, duty_u16=65535)
                _outputs.append(output)
                fans.append(output)
            print('R%d: both fans ramp to 100%% over 2s; LEDs OFF.' % reactor)
            for step in range(1, 41):
                for output in fans:
                    output.duty_u16(round(65535 * (40-step) / 40))
                sleep_ms(50)
            rpm = _measure_rpm(1000)
            _report_rpm(reactor, rpm)
            if any(speed == 0 for speed in rpm):
                print('Stopped before LEDs: both fans must report rotation.')
                return
            print('R%d: BOTH LEDs + BOTH fans at 100%% command for 2s.' % reactor)
            for gpio in LED_GPIO[start:start + 2]:
                output = PWM(Pin(gpio), freq=1000, duty_u16=0)
                _led_outputs.append(output)
                output.duty_u16(65535)
            rpm = _measure_rpm(2000)
            all_off()
            _report_rpm(reactor, rpm)
            if any(speed == 0 for speed in rpm):
                print('Stopped: missing fan feedback during combined-load stage.')
                return
            if reactor != 3:
                print('All commands off; 1-second gap.')
                sleep_ms(1000)
        print('Complete. R1..R3 checked; all outputs commanded off.')
    finally:
        all_off()


def test_3_together():
    """R1..R3 simultaneously: six fans full, six LEDs full for two seconds.

Requires heatsinks and a verified fan rail. R4 stays commanded off. Tach feedback
does not measure supply voltage, LED current, temperature or stir-bar coupling.
"""
    all_off()
    counts = [0] * 6
    handlers = []
    def make_handler(index):
        def handler(pin):
            counts[index] += 1
        return handler
    def measure(duration):
        state = disable_irq()
        try:
            before = counts[:]
            start = ticks_ms()
        finally:
            enable_irq(state)
        sleep_ms(duration)
        state = disable_irq()
        try:
            after = counts[:]
            elapsed = ticks_diff(ticks_ms(), start)
        finally:
            enable_irq(state)
        if elapsed <= 0:
            raise RuntimeError('Invalid tach measurement interval')
        scale = 60000 / (TACH_PULSES_PER_REV * elapsed)
        rpm = [(b-a)*scale for a, b in zip(before, after)]
        for reactor in (1, 2, 3):
            i = 2 * (reactor-1)
            print('R%d: STIR %.0f RPM / COOL %.0f RPM' % (reactor, rpm[i], rpm[i+1]))
        return rpm
    try:
        for index, gpio in enumerate(TACH_GPIO[:6]):
            pin = Pin(gpio, Pin.IN)
            _tach_pins.append(pin)
            handler = make_handler(index)
            handlers.append(handler)
            pin.irq(trigger=Pin.IRQ_RISING, handler=handler)
        for gpio in FAN_GPIO[:6]:
            output = PWM(Pin(gpio), freq=25000, duty_u16=65535)
            _outputs.append(output)
        print('R1 + R2 + R3: ALL SIX fans ramp to 100% over 2s; LEDs OFF.')
        for step in range(1, 41):
            for output in _outputs:
                output.duty_u16(round(65535 * (40-step) / 40))
            sleep_ms(50)
        print('Checking all six fans before enabling LEDs:')
        rpm = measure(1000)
        if any(speed == 0 for speed in rpm):
            print('Stopped before LEDs: missing fan feedback.')
            return rpm
        print('ALL SIX LEDs at 100% command + ALL SIX fans at 100% for 2s.')
        for gpio in LED_GPIO[:6]:
            output = PWM(Pin(gpio), freq=1000, duty_u16=0)
            _led_outputs.append(output)
        for output in _led_outputs:
            output.duty_u16(65535)
        rpm = measure(2000)
        if any(speed == 0 for speed in rpm):
            print('CHECK: missing fan feedback during combined-load stage.')
        return rpm
    finally:
        all_off()
        print('Complete/stopped. All outputs commanded off; supplies remain live.')


def test_reactor(reactor=1, stir_percent=30):
    """STIR -> COOL -> LED A -> LED B; one element at a time."""
    _reactor(reactor)
    results = {}
    all_off()
    try:
        print('\n=== REACTOR %d ===' % reactor)
        results['stir'] = mix(reactor, stir_percent, 3, ramp_seconds=5)
        sleep_ms(1000)
        results['cool'] = cool(reactor, 100, 3, ramp_seconds=2)
        sleep_ms(1000)
        led(reactor, 1)
        sleep_ms(2000)
        led(reactor, 2)
        sleep_ms(2000)
    finally:
        all_off()
    return results


def test_all(stir_percent=30):
    """One pass through R1..R4; about 84s, plus console overhead."""
    # Validate before beginning the sequence.
    if not isinstance(stir_percent, (int, float)) or not 0 < stir_percent <= 100:
        raise ValueError('stir_percent must be greater than 0 and at most 100')
    results = []
    all_off()
    try:
        for reactor in range(1, 5):
            results.append(test_reactor(reactor, stir_percent))
        print('\n=== FAN FEEDBACK SUMMARY (last measured RPM) ===')
        for reactor, result in enumerate(results, 1):
            stir = result['stir'][-1][0] if result['stir'] else 0
            cooling = result['cool'][-1][1] if result['cool'] else 0
            print('R%d: STIR %.0f RPM / COOL %.0f RPM' % (reactor, stir, cooling))
        print('LED results and stir-bar coupling require your observation.')
        print('This is a functional check, not a current, temperature or speed qualification.')
    finally:
        all_off()
    return results


def help_commands():
    print('test_3_together()      # R1 + R2 + R3 simultaneously, full LEDs/fans for 2s')
    print('test_3()               # R1 -> R3, both fans + both LEDs at full command for 2s')
    print('test_all()             # R1 -> R4, all four elements separately')
    print('test_all(23)           # same, using 23% stirring command')
    print('test_reactor(1)        # all four elements on R1 only')
    print('mix(1, 30, 10)         # R1 stir, 30%, 10s hold after 5s ramp')
    print('cool(1, 100, 10)       # R1 cooling, 100%, 10s hold after 2s ramp')
    print('led(1, 1) / led(1, 2)  # R1 LED A / LED B, one-second checks')
    print('all_off()             # stop commands; fan/LED supply connections stay live')
    print('Ctrl+C interrupts a test and invokes cleanup. Disconnect 12V, external 5V, then USB before cable changes.')


def main():
    try:
        all_off()
        print('\nSDL4 Rev A -- FOUR-REACTOR INDIVIDUAL SYSTEM CHECK')
        print('Connect ribbons with ALL supplies disconnected. Heatsinks fitted, blades clear.')
        print('USB first: establish idle; then external 5V, then 12V. Disconnect USB LAST.')
        print('Stock board: selector 2-3. Modified external-5V board: NO selector jumper.')
        print('Watch LED reflections; keep the magnet carriers contained.')
        print('TEST runs STIR 30% (5s ramp), COOL 100% (2s ramp), then LEDs A/B separately on R1..R4.')
        command = input('Type TEST to start, or Enter for manual commands: ').strip().upper()
        if command == 'TEST':
            test_all()
        else:
            print('Idle; no automatic test started.')
    except KeyboardInterrupt:
        print('\nStopped.')
    finally:
        all_off()
    help_commands()


if __name__ == '__main__':
    main()
