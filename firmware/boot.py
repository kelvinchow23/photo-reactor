"""SDL4-0001 PCB Rev A startup idle. Save this file ON THE PICO as boot.py.

Commands fans to 0% and LEDs off as soon as MicroPython executes this file.
Does NOT prevent fan operation during hardware reset / before MicroPython starts,
or physically isolate fan power. Existing Rev A gate pull-downs default fans on.
No automatic test or network setup belongs in this startup file.
"""
from machine import Pin

# Gate HIGH turns the board's inverting fan transistor on, holding fan PWM LOW.
for gpio in (2, 3, 6, 7, 10, 11, 14, 15):
    Pin(gpio, Pin.OUT, value=1)
for gpio in (0, 1, 4, 5, 8, 9, 12, 13):
    Pin(gpio, Pin.OUT, value=0)
