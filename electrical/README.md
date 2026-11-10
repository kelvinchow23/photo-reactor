# Custom PCBs

PCB parts for the **Photoreactor Rev B** project. Both physical PCB revisions are
**Rev A**, dated 2026-10-08.

| Part | Native KiCad project | Fabrication and assembly files |
| --- | --- | --- |
| SDL4-0001 photoreactor-controller | [Open project](designs/controller/photoreactor_quad.kicad_pro) | [Rev A package](outputs/controller/SDL4-0001_photoreactor-controller_Rev-A_2026-10-08/) |
| SDL4-0002 photoreactor-led | [Open project](designs/led_board/photoreactor_led.kicad_pro) | [Rev A package](outputs/led_board/SDL4-0002_photoreactor-led_Rev-A_2026-10-08/) |

The controller serves four reactors. Each reactor uses two identical LED/fan
boards, linked by a custom harness. Native schematics and layouts are the design
sources; libraries are shared under `libraries/`.

## Useful files

- [Wiring diagram](docs/wiring/photoreactor-wiring.pdf) and [editable draw.io file](docs/wiring/photoreactor-wiring.drawio)
- [Controller assembly BOM](outputs/controller/SDL4-0001_photoreactor-controller_Rev-A_2026-10-08/SDL4-0001_photoreactor-controller_Rev-A_2026-10-08_BOM.csv)
- [LED-board assembly BOM](outputs/led_board/SDL4-0002_photoreactor-led_Rev-A_2026-10-08/SDL4-0002_photoreactor-led_Rev-A_2026-10-08_BOM.csv)
- [DigiKey bulk-import list](outputs/procurement/2026-10-15/DigiKey-bulk-import.txt) and [shopping guide](outputs/procurement/2026-10-15/shopping-guide.html)
- [Mechanical STEP assemblies and previews](outputs/mechanical/Rev-A/SDL4_REV_A_mechanical-models.zip)
- [Thermal guidance](docs/THERMAL_PLAN.md)
- [Bench test firmware](../firmware/README.md) and [observed results](../docs/bench-results.md)

Heatsink contact area is included in the LED mechanical model. Component envelopes
are simplified and mating plugs/wire bends require additional clearance.

## Maintenance

Helper code belongs in [automation](automation/README.md), not in design folders.
Test/export commands preserve native PCB geometry. Validation outputs go to a
separate ignored folder; existing Rev A manufacturing packages are not overwritten.

This is a functionally exercised prototype, not a thermally qualified design.

## Output naming

Release folders and deliverable filenames use
`<part-number>_<part-name>_Rev-<revision>_<YYYY-MM-DD>`, followed by the
file purpose, such as `_Gerbers.zip`, `_BOM.csv`, `_CPL.csv` or `_board-only.step`.
The date records completion of that PCB release; it is not the date of a later
file rename or documentation update. Current PCB releases were completed 2026-10-08.
Native design files and the Gerber filenames inside the fabrication ZIPs retain
their original names.
