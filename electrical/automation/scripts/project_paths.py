"""Resolve project inputs while preserving isolated mutation-test fixtures."""
from pathlib import Path
import os
PCB_ROOT = Path(__file__).resolve().parents[2]
DESIGNS = {'quad': 'controller', 'led': 'led_board'}
REVISIONS = {'quad': 'SDL4-0001_photoreactor-controller_Rev-A_2026-10-08', 'led': 'SDL4-0002_photoreactor-led_Rev-A_2026-10-08'}
def design_dir(design):
    return PCB_ROOT/'designs'/DESIGNS[design]
def output_dir(design):
    validation_root = os.environ.get('PHOTO_REACTOR_VALIDATION_DIR')
    if validation_root:
        return Path(validation_root)/DESIGNS[design]
    return PCB_ROOT/'outputs'/DESIGNS[design]/REVISIONS[design]
def source_path(name):
    local=Path(name)
    if local.exists(): return local
    if name.endswith('.py'): return Path(__file__).parent/name
    if name.endswith('.net') and (PCB_ROOT/'automation/netlists'/name).exists():
        return PCB_ROOT/'automation/netlists'/name
    for key,folder in DESIGNS.items():
        if name.startswith('photoreactor_'+key+'.') or name.startswith('photoreactor_'+key+'_'):
            return PCB_ROOT/'designs'/folder/name
    raise FileNotFoundError(name)
