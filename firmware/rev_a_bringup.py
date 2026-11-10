"""SDL4-0001 Rev A: initial controller checks, with reactor cables unplugged.

Run with MicroPython on the original Pico / Pico H. Save on the Pico as
main.py so the output states are initialized after a restart.
This deliberately provides NO command to enable an LED.
GPIO numbers below are GPIO identifiers, not physical header pin numbers.
"""
from machine import Pin

# Order: reactor 1 A/B, reactor 2 A/B, reactor 3 A/B, reactor 4 A/B.
LED_GPIO = (0, 1, 4, 5, 8, 9, 12, 13)
FAN_GPIO = (2, 3, 6, 7, 10, 11, 14, 15)
TACH_GPIO = (16, 17, 18, 19, 20, 21, 22, 26)

# A low LED control commands off. A HIGH fan transistor gate pulls the
# external PWM wire LOW (inverted output). This is a PWM command, not
# a disconnection of fan power or a guarantee that any given fan stops.
led_controls = [Pin(gpio, Pin.OUT, value=0) for gpio in LED_GPIO]
fan_controls = [Pin(gpio, Pin.OUT, value=1) for gpio in FAN_GPIO]
tach_inputs = [Pin(gpio, Pin.IN) for gpio in TACH_GPIO]


def all_off():
    """LED controls low; fan PWM wires pulled low. Fan supply stays live."""
    for output in led_controls:
        output.value(0)
    for output in fan_controls:
        output.value(1)


def r1_tach():
    """Return static input levels; these are not RPM measurements."""
    result = (tach_inputs[0].value(), tach_inputs[1].value())
    print("R1 tach input levels (stir, cool):", result)
    return result


all_off()
print("Rev A initial checks: all LED controls OFF.")
print("Keep all reactor cables disconnected. No LED-enable command is provided.")
print("R1: pin 8=GND; 7=fan supply; 5/6=tach; 9/10=fan PWM.")
print("With Pico powered, pin 5/6 should be about 3.3V, 9/10 about 0V.")
print("USB alone does NOT power the controller 5V/fan supply rail.")
print("Use all_off() to reassert outputs, or r1_tach() to read static inputs.")
