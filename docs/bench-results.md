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

- Fan channels on reactor ports 2-4; only their LED channels were exercised.
- 5V at the fan under full-speed load and the full-speed RPM discrepancy.
- LED current, startup/turn-off behaviour, dimming range and control ripple.
- Sustained thermal operation with electrically insulating TIM, heatsinks and clamps.
- Mechanical fit of the new housing and cable/connector clearances.
- Safe sustained-operation firmware, communications timeout and fault handling.

Future Linux/Compute Module, sensor and connector redesigns are proposals. The
published Rev A PCB remains the Pico-based design tested above.
