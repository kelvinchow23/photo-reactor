"""Export/check authoritative KiCad schematics. Never regenerate PCB placement."""
import os
from pathlib import Path
import subprocess
import shutil
import sys
import argparse

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', help='Validation output directory; defaults to electrical/outputs/validation/latest')
args = parser.parse_args()
validation_dir = Path(args.output_dir).resolve() if args.output_dir else ROOT.parent/'outputs/validation/latest'
for folder, release_name in [('controller', 'SDL4-0001_photoreactor-controller_Rev-A_2026-10-08'), ('led_board', 'SDL4-0002_photoreactor-led_Rev-A_2026-10-08')]:
    release_dir = (ROOT.parent/'outputs'/folder/release_name).resolve()
    if validation_dir == release_dir or release_dir in validation_dir.parents:
        raise SystemExit('Validation outputs must not overwrite the Rev-A package.')
os.environ['PHOTO_REACTOR_VALIDATION_DIR'] = str(validation_dir)
os.environ.setdefault('KICAD_DOCUMENTS_HOME', str(ROOT/'kicad-user-docs'))
os.environ.setdefault('KICAD_CONFIG_HOME', str(ROOT/'kicad-export-config'))
sys.path.insert(0, str(ROOT/'scripts'))
from project_paths import design_dir, output_dir
os.chdir(ROOT/'scripts')
if 'KICAD_SYMBOL_DIR' not in os.environ:
    candidates = sorted(Path('C:/Program Files/KiCad').glob('*/share/kicad'), reverse=True)
    base = candidates[0] if candidates else Path('/usr/share/kicad')
    os.environ['KICAD_SYMBOL_DIR'] = str(base / 'symbols')
os.environ.setdefault('KICAD_FOOTPRINT_DIR', str(Path(os.environ['KICAD_SYMBOL_DIR']).parent / 'footprints'))
os.environ['KICAD8_SYMBOL_DIR'] = os.environ['KICAD_SYMBOL_DIR']
os.environ['PYTHONUTF8'] = '1'

def run(*args):
    subprocess.run([sys.executable, *args], check=True)

cli = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli')
if not cli:
    candidates = sorted(Path('C:/Program Files/KiCad').glob('*/bin/kicad-cli.exe'), reverse=True)
    cli = str(candidates[0]) if candidates else None
if not cli:
    raise SystemExit('Install KiCad 10 or set KICAD_CLI to kicad-cli.')
(ROOT/'netlists').mkdir(exist_ok=True)
for design in ('quad', 'led'):
    sch=str(design_dir(design)/f'photoreactor_{design}.kicad_sch')
    reports=output_dir(design)/'reports'
    reports.mkdir(parents=True,exist_ok=True)
    subprocess.run([cli,'sch','erc','--exit-code-violations','--format','json',
                    '--output',str(reports/f'{design}-erc.json'),sch],check=True)
    subprocess.run([cli,'sch','export','netlist','--output',str(ROOT/'netlists'/f'photoreactor_{design}.net'),sch],check=True)
    run('mkbom.py', design)
run('verify_quad.py')
run('verify_paired.py')
run('-m', 'unittest', '-v', 'test_regressions', 'test_paired')
print('Schematic ERC, netlist, BOM and regression checks passed. PCB files were not regenerated.')
