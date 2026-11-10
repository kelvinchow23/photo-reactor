"""Manual one-second dimmed checks of all eight LEDs, SDL4-0001 Rev A.

Save this file on the Pico as main.py. It starts with every LED OFF and
never lights an LED automatically on boot. In Thonny's Shell call check(1)
through check(8). Channels 1/2 = reactor 1, 3/4 = reactor 2,
5/6 = reactor 3, and 7/8 = reactor 4.
Disconnect 12V before moving cables. Aim LEDs away and observe reflected
light; the dimming setting is not a certified eye-safe viewing level.
No fans or heatsinks are required for this brief indication
check; this is not a thermal qualification or permission for continuous use.
"""
from machine import Pin, PWM
from time import sleep_ms

LED_GPIO = (0, 1, 4, 5, 8, 9, 12, 13)
FAN_GPIO = (2, 3, 6, 7, 10, 11, 14, 15)
TACH_GPIO = (16, 17, 18, 19, 20, 21, 22, 26)


def all_off():
    for gpio in LED_GPIO:
        Pin(gpio, Pin.OUT, value=0)
    # Gate HIGH pulls external fan PWM LOW. Fan supply remains live.
    for gpio in FAN_GPIO:
        Pin(gpio, Pin.OUT, value=1)


all_off()
tach_inputs = [Pin(gpio, Pin.IN) for gpio in TACH_GPIO]


def check(channel):
    """Check LED channel 1..8, at fixed dimming/time.

20% GPIO duty is filtered by the fitted 3k3/10k/1uF CTRL network.
It is NOT a measured 20% optical output or a calibrated LED current.
"""
    if type(channel) is not int or not 1 <= channel <= 8:
        raise ValueError("channel must be an integer from 1 to 8")
    reactor = (channel - 1) // 2 + 1
    board = (channel - 1) % 2 + 1
    all_off()
    pwm = None
    try:
        pwm = PWM(Pin(LED_GPIO[channel - 1]))
        pwm.duty_u16(0)
        pwm.freq(1000)
        print("Reactor", reactor, "LED board", board, "-- one-second dimmed check")
        pwm.duty_u16(13107)  # Fixed 20% GPIO duty; do not increase for this check.
        sleep_ms(1000)
    finally:
        if pwm is not None:
            pwm.duty_u16(0)
            pwm.deinit()
        all_off()
    # Avoid rapid repeat tests and allow the LED to cool.
    sleep_ms(10000)
    print("OFF. Check complete.")


print("All LEDs OFF. Use check(1) through check(8).")
print("R1: 1/2; R2: 3/4; R3: 5/6; R4: 7/8.")
print("Disconnect 12V before moving cables.")
print("Each check lights one LED briefly, then waits 10 seconds before returning.")
