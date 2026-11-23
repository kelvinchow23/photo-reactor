# Pico firmware — PCB Rev A

MicroPython bench checks and a demonstration for the original Pico / Pico H on
SDL4-0001, with two SDL4-0002 LED/fan boards per reactor. The overall project is
Rev B; these programs still target **PCB Rev A**. No external Python libraries
or original upstream `photo_reactor.py` are required on the Pico.

## Start here

| File | Use |
| --- | --- |
| [rev_a_system_check.py](rev_a_system_check.py) | Recommended diagnostics: individual fans/LEDs, three reactors sequentially or simultaneously. |
| [rev_a_demo.py](rev_a_demo.py) | Approximately 23-second R1–R3 fan crescendo, light chase, blinking and a two-second full-command finale. |
| [boot.py](boot.py) | Optional early idle commands; save **on the Pico** as `boot.py`. |
| [tests/](tests/) | Computer-only simulations. **Do not upload these to the Pico.** |

The existing bench setup has three working assemblies on **R1, R2 and R3**.
R4 is excluded from `test_3()`, `test_3_together()` and `demo()`. The full
`test_all()` command intentionally includes R4; do not use it for the three-reactor setup.

## Power connections: identify your controller

| Configuration | Fan power | Selector |
| --- | --- | --- |
| Original, healthy board | Onboard 12V-to-5V buck converter | JP_FANV pins 2–3 for 5V fans |
| **Current physically modified board** | External regulated 5V; Pico powered by USB | Buck and selector removed; **NO jumper** |

On the modified board, external +5V feeds the repaired FAN_V connection formerly
JP_FANV centre pad 2; external negative must connect to **permanent controller
GND**. Neither the barrel jack switched contact nor its +12V terminal is ground.
The supplies share GND, but their positive outputs are not joined. Verify fan
supply near 5V between reactor connector pins **7 (+)** and **8 (GND)** with 12V
present. This setup previously suffered a return-wiring error and about 17V at
fans; one fan was damaged. Original buck failures remain unresolved.

**Never plug/unplug reactor ribbons, fans, the Pico or jumpers while powered.**
Fit heatsinks, contain rotating magnets, and observe LED reflections rather than
looking into the emitters. These scripts are for the existing green LEDs, not a
qualified UV setup or unattended operation.

## Start up in Thonny

1. Disconnect **12V, external 5V and USB**. Connect the intended reactor harnesses.
2. Connect Pico **USB first**. Select the MicroPython Raspberry Pi Pico interpreter
   and the correct port in Thonny.
3. Open `rev_a_system_check.py` on your computer and press Run/F5. At its prompt,
   press **Enter** for manual mode. It establishes all-off commands.
4. Connect external **5V**, then **12V**. For an original unmodified board there
   is no separate external 5V connection.
5. Enter one command from the table below in the Thonny Shell.

Use **one program at a time**. To switch to the demo or another script, disconnect
12V and external 5V while keeping USB connected, run the new file, establish idle,
then reconnect external 5V and 12V. Do not run a host `test_*.py` file in Thonny.

## Save on the Pico (optional)

In Thonny select **View → Files** after choosing the MicroPython Pico interpreter.
The file panel shows both the computer and Raspberry Pi Pico. Open `boot.py` on
this computer, then **File → Save as → Raspberry Pi Pico → boot.py**. Back up any
existing file before replacing it.

Save either `rev_a_system_check.py` or `rev_a_demo.py` onto the Pico as **main.py**
if you want that program to start after reset. Only one can have that name. Both
wait for a serial prompt before running a sequence; neither auto-starts the
lights. Keep the other program under its original name if desired, or simply
run it from the computer in Thonny. Do not copy the `tests/` folder to the Pico.
USB must still be connected first and removed last on the modified controller.

## Diagnostic commands

After running `rev_a_system_check.py` and pressing Enter:

| Command | Behavior |
| --- | --- |
| `mix(1, 30, 10)` | R1 stirring only; 5-second ramp to 30%, then 10-second hold; RPM feedback. |
| `cool(1, 100, 10)` | R1 cooling only; 2-second ramp to 100%, then 10-second hold; RPM feedback. |
| `led(1, 1)` | R1 LED A, one second at 20% GPIO duty; fans commanded off. |
| `led(1, 2)` | R1 LED B, same. |
| `test_reactor(1)` | STIR, COOL, LED A, LED B individually on R1. |
| `test_3()` | R1 → R2 → R3: ramp both fans, check tach, then both LEDs and fans at full command for 2 seconds; 1-second gaps. |
| `test_3_together()` | R1 + R2 + R3 simultaneously: ramp six fans, check six tach inputs, then six LEDs and fans at full command for 2 seconds. |
| `test_all()` | All four ports, four elements separately per reactor; approximately 84 seconds. |
| `all_off()` | Reassert off commands; **does not remove supply power**. |

For individual commands, the first argument selects reactor 1–4. Fan percentage
is a PWM command, not a calibrated RPM or torque. Three consecutive one-second
zero-feedback windows stop an individual fan test. Combined tests require both/all
active fans to report tach feedback before enabling LEDs. Tach indicates rotation,
not stir-bar coupling, airflow or acceptable temperature.

Commands stop their outputs when they finish. Normal **Ctrl+C** interruption also
invokes cleanup. You do not need to append `all_off()` after every command.

## Demonstration

Open `rev_a_demo.py`, run it, and establish idle before applying fan/LED power.
Type **DEMO** at the prompt, or press Enter then type `demo()`.

One pass adds stirring fans R1 → R2 → R3, then cooling fans R1 → R2 → R3,
keeping earlier fans running. All six fans reach 100%. The LEDs chase forward
and backward, alternate sides, blink together, then finish at 100% command for
two seconds. Earlier light patterns use 20% GPIO duty. All lights go off, final
fan feedback is reported, fans run for two further seconds, then off commands
are applied. The script checks tach before the light show and after it; it does
not continuously supervise faults. There is no automatic repeat. Use `demo()`
to repeat or Ctrl+C to stop.

## Shut down — USB last

1. Let the command finish, or press Ctrl+C. `all_off()` can repeat the off commands.
2. Disconnect **12V**.
3. Disconnect **external 5V**.
4. Disconnect **USB last**.

Removing USB while external fan power remains connected can make the fans run:
the Pico stops driving their control inputs and Rev A hardware defaults toward
fan-on. This cannot be fixed by a script after the Pico loses power. All-off
commands do not cover resets, firmware crashes or electrical faults.

Optional: save `boot.py` onto the Pico as `boot.py`, backing up/merging any
existing file first. It commands idle once MicroPython executes it, but cannot
prevent fan-on before startup. Keep bench programs on the computer initially;
there is no need to install a `main.py` or an auto-running demo. Inspect any old
`main.py` already on the Pico before independent power-cycle testing.

## Electrical limits and known gaps

LED channels use AL8860 constant-current drivers and 0.43Ω sense resistors for
approximately **233mA maximum nominal LED current**. GPIO PWM at 1kHz is filtered
through the PCB divider/capacitor into analog dimming. 20% duty is not measured
20% light output; 100% is full command, not an override of the current limit.

Short combined tests and a demo are not sustained thermal qualification. The
repaired fan-power trace, startup current, loaded voltage drop and temperatures
still need validation. There is no software voltage/current/temperature sensor,
hardware interlock or guaranteed hardware default-off. Host tests do not validate
the actual PWM peripheral, damaged copper, supply protection or wiring.

## Developer checks

On your **computer**, from the repository root:

```sh
python -m unittest discover -s firmware/tests -p "test_*.py" -v
```

Tests simulate channel selection, inverted fan PWM, two-pulse/revolution tach
math, sequences, missing feedback and interruption cleanup. They are not
MicroPython programs to flash. Preserve standalone operation of each bench
script when making changes. Hardware facts and observed results are also recorded
in [bench results](../docs/bench-results.md); native PCB sources remain authoritative.
