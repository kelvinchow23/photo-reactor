# PCB maintenance

These helpers check or export the two native KiCad designs. They do not generate
placement/routing or replace the editable schematics.

```sh
python -m unittest discover -s electrical/automation/scripts -p "test_*.py" -v
python electrical/automation/build.py
```

The first command runs 20 connectivity/geometry regression tests. The second
requires KiCad 10: it runs schematic ERC, exports current netlists and engineering
BOMs, and runs the regression suite. Validation reports/BOMs go under
`electrical/outputs/validation/latest`, not into the Rev A manufacturing package.
`--output-dir` selects another non-release destination. `KICAD_CLI` can select the
KiCad executable. Generated netlists under `netlists/` are used by the tests.

- `scripts/`: maintained connectivity, geometry and engineering-BOM helpers.
- `mechanical_export/`: component-envelope STEP exporter and dependency notes.

The exact JLC assembly BOM/CPL and rotation offsets are retained in the revisioned
output packages. An engineering BOM from this check command is not an assembly
upload or a claim about current supplier stock.
