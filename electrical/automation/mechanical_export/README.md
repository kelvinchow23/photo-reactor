# Mechanical STEP export

`build.py` creates dimension-based mechanical assembly models and preview images
from the native PCB component positions and the board-only STEP exports. It does
not edit native layouts, schematics, routing, BOMs or Gerbers.

The script uses Python 3.12, the Open Cascade Python bindings, NumPy and Pillow.
Local copies of third-party libraries are ignored by Git:

```sh
python -m pip install --target electrical/automation/mechanical_export/deps_stable -r electrical/automation/mechanical_export/requirements.txt
python electrical/automation/mechanical_export/build.py
```

Run from the repository root. KiCad 10's installed
`Module.3dshapes/RaspberryPi_Pico_H.step` is needed. `KICAD_3DMODEL_DIR` can point to
the installed 3D model directory; Windows and Linux defaults are detected.
`PHOTOREACTOR_FONT` can select a TrueType font for the previews; otherwise the
script detects a common system font or uses Pillow's default.

Inputs are `outputs/<board>/<part-number>_<part-name>_Rev-A_2026-10-08/step/*board-only.step`. The exporter uses nominal
finished board thickness for enclosure references and preserves native PCB geometry.
The LED optical dome, connector details and other envelopes are simplified, not
vendor-certified models. The heatsink clearance is a separate reference volume.
See the delivered `MECHANICAL-MODELS.txt` for interpretation and limitations.

One-time reference downloads, installed CAD libraries and local working data are
not part of the publish set. Mechanical dimension sources are under
`electrical/docs/references/`. Generated STEP files and previews remain under the board's
revisioned `outputs` directory.
