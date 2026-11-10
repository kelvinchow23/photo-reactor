# SDL4-0002 photoreactor-led - PCB Rev A

Part of Photoreactor project Rev B. Board identification: Rev A, 2026-10-08.
Package notes updated 2026-11-10; manufacturing files are unchanged.

Use `SDL4-0002_photoreactor-led_Rev-A_2026-10-08_Gerbers.zip`, `SDL4-0002_photoreactor-led_Rev-A_2026-10-08_BOM.csv` and `SDL4-0002_photoreactor-led_Rev-A_2026-10-08_CPL.csv` together.
Seven fitted parts: D1 on top; C1, C2, R1, J1, J2 and J3 on bottom. Select
**both-side assembly**. Mounting holes and the bare thermal contact are not BOM
parts. CPL J1/J2/J3 rotations include assembly-preview corrections; do not apply
these as native footprint edits. Check supplier placement/polarity before ordering.

D1: XINGLIGHT XL-HD6070UGC-A2-BD / C42458855. Specified wavelength range is
520-530nm; the ordered wavelength bin is not established here. Pad 1 is anode,
pad 2 cathode. CAD pad 3 denotes the unnumbered thermal land. The thermal copper
is separate from ground and may be live; use electrically insulating TIM.

The supplier drawing specifies one reflow at up to 220C for 6s. A successful
prototype is not proof that a generic two-sided reflow process meets that limit.
J1 uses a generic native land pattern that differs from the recommended JXTC
lands; supplier acceptance is required before repeating the order.

[Native KiCad project](../../../designs/led_board/photoreactor_led.kicad_pro),
[mechanical assembly STEP](step/SDL4-0002_photoreactor-led_Rev-A_2026-10-08_mechanical-assembly.step),
[thermal guidance](../../../docs/THERMAL_PLAN.md), and
[bench results](../../../../docs/bench-results.md).

The same board is used twice per reactor. First OUT connects to second IN using
the documented six-to-ten-pin harness; second OUT remains empty. Nominal paired
controller current is approximately 233mA per LED. Sustained thermal/current
performance remains unqualified.
