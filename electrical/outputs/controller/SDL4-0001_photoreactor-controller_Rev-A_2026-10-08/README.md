# SDL4-0001 photoreactor-controller - PCB Rev A

Part of Photoreactor project Rev B. Board identification: Rev A, 2026-10-08.
Package notes updated 2026-11-10; manufacturing files are unchanged.

Use `SDL4-0001_photoreactor-controller_Rev-A_2026-10-08_Gerbers.zip`, `SDL4-0001_photoreactor-controller_Rev-A_2026-10-08_BOM.csv` and
`SDL4-0001_photoreactor-controller_Rev-A_2026-10-08_CPL.csv` together. The assembly package contains 148 SMT
placements in 30 BOM groups. CPL rotations include JLC-specific offsets; do not
apply them to native KiCad footprints or apply them twice.

Hand-fit the Pico/socket strips, Wurth 694106301002 power jack and fan-voltage
jumper cap. The specified fans are 5V: JP_FANV pins 2-3 only.
C6/C7 are TCC1210X7R226K250MT / C49118556, 22uF 25V X7R 1210.

[Native KiCad project](../../../designs/controller/photoreactor_quad.kicad_pro)
and [mechanical assembly STEP](step/SDL4-0001_photoreactor-controller_Rev-A_2026-10-08_mechanical-assembly.step).
Historical DRC reports are in `reports/`. Current functional observations are in
[bench results](../../../../docs/bench-results.md). Current/thermal operation and
full-speed fan performance remain to be validated.
