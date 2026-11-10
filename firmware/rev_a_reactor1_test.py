"""SDL4-0001 Rev A / original Pico H: two LEDs and two fans on REACTOR 1.

Standalone MicroPython program; no other project files are needed on the Pico.
Run in Thonny. Outputs start off; type TEST at the prompt to start the full test.
Do not save over a working production program without keeping a copy.

CFM-2006CF-060-078-22: 5V, 25kHz PWM here, two tach pulses/revolution.
First LED board = LED 1 / stir fan; second board = LED 2 / cooling fan.
JP_FANV must bridge 2-3 (5V). Switch off 12V before changing cables.
LED checks are fixed, brief indication checks, not thermal qualification.
"""
from machine import Pin, PWM, disable_irq, enable_irq
from time import sleep_ms, ticks_ms, ticks_diff
import micropython

micropython.alloc_emergency_exception_buf(100)

LED_GPIO = (0, 1, 4, 5, 8, 9, 12, 13)
FAN_GPIO = (2, 3, 6, 7, 10, 11, 14, 15)
TACH_GPIO = (16, 17)
FAN_HZ = 25000
LED_HZ = 1000
LED_TEST_DUTY = 13107  # 20% GPIO duty; not calibrated light output.
TACH_PULSES_PER_REV = 2

_led_pwm = [None, None]
_fan_pwm = [None, None]
_tach_counts = [0, 0]
_tach_pins = []


def all_off():
    """LEDs off; fan PWM commanded 0%. Does not disconnect the fan supply.

Some fans retain a minimum speed at 0% PWM. Disconnect 12V for a physical
power-off. Pin reinitialization removes PWM pin multiplexing on RP2040.
"""
    for outputs, duty in ((_led_pwm, 0), (_fan_pwm, 65535)):
        for i in range(2):
            output = outputs[i]
            if output is not None:
                try:
                    output.duty_u16(duty)
                finally:
                    try:
                        output.deinit()
                    finally:
                        outputs[i] = None
    for gpio in LED_GPIO:
        Pin(gpio, Pin.OUT, value=0)
    for gpio in FAN_GPIO:
        # 2N7002 inverts the signal: gate HIGH pulls the fan PWM wire LOW.
        Pin(gpio, Pin.OUT, value=1)


# Initialize every channel, including unused reactor ports, before any prompt.
all_off()


def _tach1(pin):
    _tach_counts[0] += 1


def _tach2(pin):
    _tach_counts[1] += 1


def _attach_tach():
    if not _tach_pins:
        for gpio, handler in zip(TACH_GPIO, (_tach1, _tach2)):
            pin = Pin(gpio, Pin.IN)  # External pull-ups to 3.3V are on controller.
            _tach_pins.append(pin)
            pin.irq(trigger=Pin.IRQ_RISING, handler=handler, hard=True)


def _detach_tach():
    for pin in _tach_pins:
        pin.irq(handler=None)
    _tach_pins[:] = []


def _snapshot():
    state = disable_irq()
    try:
        return ticks_ms(), _tach_counts[0], _tach_counts[1]
    finally:
        enable_irq(state)


def _measure_rpm():
    start, a0, b0 = _snapshot()
    sleep_ms(2000)
    end, a1, b1 = _snapshot()
    elapsed = ticks_diff(end, start)
    if elapsed <= 0:
        raise RuntimeError("Invalid tach measurement interval")
    scale = 60000 / (TACH_PULSES_PER_REV * elapsed)
    return ((a1 - a0) * scale, (b1 - b0) * scale)


def _set_fans(first, second):
    for i, percent in enumerate((first, second)):
        if _fan_pwm[i] is None:
            _fan_pwm[i] = PWM(Pin(FAN_GPIO[i]), freq=FAN_HZ, duty_u16=65535)
        # Convert requested HIGH duty at the FAN connector to inverted gate duty.
        _fan_pwm[i].duty_u16(round(65535 * (100 - percent) / 100))


def test_fans():
    """Run six bounded stages, then command both fans to 0% and release PWM.

Observe which fan moves as well as the reported RPM. Minimum-speed behaviour
is possible; zero PWM does not guarantee a stationary fan.
"""
    all_off()
    results = []
    stages = (
        ("STIR only, full speed", 100, 0),
        ("STIR only, reduced speed", 60, 0),
        ("COOL only, full speed", 0, 100),
        ("COOL only, reduced speed", 0, 60),
        ("BOTH, full speed", 100, 100),
        ("BOTH, reduced speed", 60, 60),
    )
    try:
        _attach_tach()
        print("\nFAN TEST: LEDs remain OFF. Keep blades clear.")
        print("Watch fan identity: STIR = first board; COOL = second board.")
        for title, first, second in stages:
            print("\n" + title)
            _set_fans(first, second)
            sleep_ms(3000)  # Startup/settling; every run begins its fan at 100%.
            rpm = _measure_rpm()
            results.append((title, first, second, rpm))
            print("Command: STIR %d%% / COOL %d%%" % (first, second))
            print("Measured: STIR %.0f RPM / COOL %.0f RPM" % rpm)
            for i, command in enumerate((first, second)):
                if command > 0 and rpm[i] == 0:
                    print("CHECK: %s has no tach pulses. If spinning, check tach wiring."
                          % ("STIR" if i == 0 else "COOL"))
                elif command == 0 and rpm[i] > 0:
                    print("NOTE: %s still reports rotation at 0%% command;"
                          " check minimum speed, coasting, or channel mapping."
                          % ("STIR" if i == 0 else "COOL"))
        print("\nFAN RESULTS (visual identity still needs your observation):")
        for label, high_index, low_index, channel in (
                ("STIR", 0, 1, 0), ("COOL", 2, 3, 1)):
            high = results[high_index][3][channel]
            low = results[low_index][3][channel]
            if high == 0 or low == 0:
                print(label + ": CHECK -- missing RPM feedback at one or both settings.")
            elif low < high * .95:
                print(label + ": RPM feedback present; reduced command reduced speed.")
            else:
                print(label + ": RPM feedback present; speed response needs checking.")
        print("No fixed RPM pass band: magnets/load and the fan tolerance affect speed.")
    finally:
        try:
            all_off()
        finally:
            _detach_tach()
        print("Fans commanded to 0%; LEDs OFF. Fan supply is still live.")
    return results


def check(channel):
    """One-second dimmed check of LED 1 or 2 on REACTOR 1 only."""
    if type(channel) is not int or channel not in (1, 2):
        raise ValueError("For this REACTOR 1 test, use check(1) or check(2)")
    all_off()
    try:
        i = channel - 1
        _led_pwm[i] = PWM(Pin(LED_GPIO[i]), freq=LED_HZ, duty_u16=0)
        print("LED %d: one-second dimmed flash. Observe reflected light." % channel)
        _led_pwm[i].duty_u16(LED_TEST_DUTY)
        sleep_ms(1000)
    finally:
        all_off()
    print("LED OFF; cooling pause (10 seconds).")
    sleep_ms(10000)


def run_test():
    """Full reactor 1 test; Ctrl+C performs normal exception cleanup."""
    try:
        test_fans()
        print("\nLED TEST: only one LED should flash at a time.")
        check(1)
        check(2)
        print("\nSequence complete. Confirm both LED identities visually.")
        print("This checks function, not LED current or sustained temperature.")
    finally:
        all_off()


def main():
    try:
        print("\nSDL4 Rev A -- REACTOR 1 TEST")
        print("All LEDs OFF; fans commanded to 0%.")
        print("Confirm JP_FANV is 2-3 (5V), both fans are clear, and all wiring is on R1.")
        print("Aim LEDs away from your eyes; watch light reflected from a matte surface.")
        print("Connect 12V now. Full test: fans about 30s, then two brief LED checks.")
        command = input("Type TEST and press Enter to start, or Enter to cancel: ").strip().upper()
        if command == "TEST":
            run_test()
        else:
            print("Cancelled; outputs remain off/0% command.")
    except KeyboardInterrupt:
        print("\nStopped by Ctrl+C.")
    finally:
        try:
            all_off()
        finally:
            _detach_tach()
    print("Shell commands: test_fans(), check(1), check(2), all_off().")
    print("Disconnect 12V for a physical power-off or before moving cables.")


if __name__ == "__main__":
    main()
