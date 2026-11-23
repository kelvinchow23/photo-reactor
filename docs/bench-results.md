# Rev A bench results

Recorded from manual bench testing reported on 4-9 November 2026. These are
prototype observations, not production qualification or independent measurements.

## Confirmed function

- Controller reactor-port fan supply measured approximately 5V with JP_FANV at 2-3.
- Reactor 1 tach pull-ups and static fan-control voltage checks behaved as expected.
- One pair of LED boards and its custom harness was moved across all four controller
  ports. All eight independent LED commands produced the expected brief illumination
  at the test's 20% GPIO duty setting and switched off afterward.
- Lowering the dimming command produced visibly lower output. Channel 8 did not
  illuminate at 12%, although it previously worked at 20%. No failure was established;
  low-end threshold and channel matching remain uncharacterized.
- Both fans on REACTOR 1 produced tach feedback and independently responded to
  100% and 60% commands. Simultaneous operation also produced both RPM readings.

## Reactor 1 fan readings

Second reported run, 9 November 2026. RPM assumes the specified fan's two tach
pulses per revolution; the test counts rising edges over two seconds.

| Command | Stir RPM | Cooling RPM |
| --- | ---: | ---: |
| Stir 100%, cooling 0% | 3750 | 0 |
| Stir 60%, cooling 0% | 2175 | 0 |
| Stir 0%, cooling 100% | 0 | 4050 |
| Stir 0%, cooling 60% | 0 | 2415 |
| Both 100% | 4095 | 4230 |
| Both 60% | 2355 | 2520 |

An earlier run reported full-speed values of approximately 4095-4575 RPM.
The nominal fan specification is 6000 RPM +/-20% under the manufacturer's test
conditions. Loaded supply voltage, fan load, settling, RPM measurement accuracy
and full-speed performance have not been resolved. These logs support functional
PWM/tach operation, not a rated-speed acceptance claim.

## Still to validate

The following original list predates the later observations below; it is retained
as the scope of the initial checks, not the latest status of every port.

- Fan channels on reactor ports 2-4; only their LED channels were exercised.
- 5V at the fan under full-speed load and the full-speed RPM discrepancy.
- LED current, startup/turn-off behaviour, dimming range and control ripple.
- Sustained thermal operation with electrically insulating TIM, heatsinks and clamps.
- Mechanical fit of the new housing and cable/connector clearances.
- Safe sustained-operation firmware, communications timeout and fault handling.

Future Linux/Compute Module, sensor and connector redesigns are proposals. The
published Rev A PCB remains the Pico-based design tested above.

## Later bring-up and modified controller (updated 2026-11-23)

- Later fans-only logs reported tach feedback from all eight channels across R1–R4.
  Two-second stage averages included startup and did not establish settled speed.
- Stronger Wakefield DC0401005V2B-BT0 5V stirring fans were introduced. Slow fan
  ramps improved startup with the printed magnet carrier and magnetic load.
- Two controllers developed power faults. On one, a roughly 2Ω 5V-to-ground fault
  cleared after U_BUCK removal. Original converter failure causes remain unknown;
  a powered ribbon connection preceded a failure on the other board.
- The current controller physically has U_BUCK and JP_FANV removed. External 5V
  feeds FAN_V, USB powers the Pico, and 12V powers the LED drivers. This physical
  bypass is not a change to the released native CAD or manufacturing files.
- External supply negative was first connected through the jack switched contact;
  inserting an unpowered plug changed ground continuity from about 0.2Ω to about
  1MΩ. A later move to +12V instead of GND produced approximately 17V at the fan
  rail. One fan was damaged. These later wiring errors do not explain the earlier
  onboard-converter failures.
- After correcting the permanent ground return, the user reported successful
  R1–R3 combined LED/fan operation at full command, one reactor at a time for two
  seconds. Simultaneous three-reactor and demo scripts were subsequently supplied;
  their host simulation results must not be reported as physical acceptance.
- With external fan power present, removing USB makes fans run because the
  unpowered Pico no longer holds the stop signal. Shutdown is 12V off, external
  5V off, USB last. All power must be removed before wiring changes.

Sustained temperatures, LED current/optical calibration, loaded fan-rail voltage,
startup current and repaired-trace capacity remain unqualified. No unattended
operation or UV conversion has been validated. See the [firmware guide](../firmware/README.md)
for the current operator procedure and distinction between stock and modified boards.
