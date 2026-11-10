"""Prove the corrected checks reject the actual review defects.

Mutations run against disposable copies; production netlists/boards are not edited.
Run after build.py with: python -m unittest -v test_regressions
"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from project_paths import source_path

ROOT = Path(__file__).resolve().parent


def parse(text):
    tokens = iter(re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text))
    def node():
        out = []
        for t in tokens:
            if t == ')': return out
            out.append(node() if t == '(' else t)
        return out
    return node()[0]


def dump(n):
    return '(' + ' '.join(map(dump, n)) + ')' if isinstance(n, list) else n


def child(n, key):
    return next(x for x in n if isinstance(x, list) and x[0] == key)


class ReviewRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        for name in ('photoreactor_quad.net', 'photoreactor_quad.kicad_pcb',
                     'verify_quad.py', 'validate_pcb.py', 'pico_geometry.py', 'project_paths.py'):
            shutil.copy2(source_path(name), self.path / name)

    def check_script(self, script, *args, fail=False, message=''):
        p = subprocess.run([sys.executable, script, *args], cwd=self.path,
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 1 if fail else 0, p.stdout + p.stderr)
        if fail:
            self.assertIn(message, p.stdout)
            self.assertNotIn('Traceback', p.stderr)

    def move_pins(self, filename, assignments):
        path = self.path / filename
        tree = parse(path.read_text())
        nets = child(tree, 'nets')[1:]
        by_name = {child(n, 'name')[1].strip('"'): n for n in nets}
        for (ref, pin), destination in assignments.items():
            found = []
            for net in nets:
                for node in net[:]:
                    if isinstance(node, list) and node[0] == 'node':
                        if child(node, 'ref')[1].strip('"') == ref and child(node, 'pin')[1].strip('"') == pin:
                            net.remove(node); found.append(node)
            self.assertEqual(len(found), 1, (ref, pin))
            by_name[destination].append(found[0])
        path.write_text(dump(tree))

    def test_corrected_baseline(self):
        self.check_script('verify_quad.py')
        self.check_script('validate_pcb.py', 'quad')

    def test_old_current_setting_rejected(self):
        path = self.path / 'photoreactor_quad.net'
        tree = parse(path.read_text())
        part = next(c for c in child(tree, 'components')[1:] if child(c, 'ref')[1].strip('"') == 'R5')
        child(part, 'value')[1] = '"0R30"'
        path.write_text(dump(tree))
        self.check_script('verify_quad.py', fail=True, message='current sense must be 0R43')

    def test_wrong_led_catch_diode(self):
        self.move_pins('photoreactor_quad.net', {
            ('D_LED1', '1'): 'LED1_SW', ('D_LED1', '2'): 'GND'})
        self.check_script('verify_quad.py', fail=True, message='FAIL U_LED1 catch diode')

    def test_grounded_led_return(self):
        self.move_pins('photoreactor_quad.net', {('J_R1', '2'): 'GND'})
        self.check_script('verify_quad.py', fail=True, message='FAIL')

    def test_reversed_tvs(self):
        self.move_pins('photoreactor_quad.net', {
            ('D_TVS', '1'): 'GND', ('D_TVS', '2'): '+12V'})
        self.check_script('verify_quad.py', fail=True, message='FAIL unidirectional TVS')

    def test_reversed_pmos(self):
        self.move_pins('photoreactor_quad.net', {
            ('Q_REV', '2'): 'VIN_FUSED', ('Q_REV', '3'): '+12V'})
        self.check_script('verify_quad.py', fail=True, message='FAIL reverse PMOS')

    def test_gate_clamp_on_input(self):
        self.move_pins('photoreactor_quad.net', {('D_GZ', '1'): 'VIN_FUSED'})
        self.check_script('verify_quad.py', fail=True, message='FAIL gate clamp')

    def test_original_cutout_removes_socket_pads(self):
        path = self.path / 'photoreactor_quad.kicad_pcb'
        tree = parse(path.read_text())
        def ref(fp):
            return next((x[2].strip('"') for x in fp if isinstance(x,list) and ((x[0]=='property' and x[1]=='"Reference"') or (x[0]=='fp_text' and x[1]=='reference'))),None)
        pico=next(n for n in tree if isinstance(n,list) and n[0]=='footprint' and ref(n)=='J_PICO')
        at=child(pico,'at');cx,cy=float(at[1]),float(at[2])
        for n in tree:
            if not isinstance(n,list) or n[0]!='gr_line':continue
            if child(n,'layer')[1].strip('"')!='Edge.Cuts':continue
            for key in ('start','end'):
                pt=child(n,key);x,y=float(pt[1]),float(pt[2])
                if x in (cx-7,cx+7) and y in (cy+16.5,cy+25.5):
                    pt[1]=str(cx-10.5 if x==cx-7 else cx+10.5)
                    pt[2]=str(cy-25.5 if y==cy+16.5 else cy-15.5)
        path.write_text(dump(tree))
        self.check_script('validate_pcb.py', 'quad', fail=True,
                          message='J_PICO pad 1 intersects cutout')

    def test_generated_board_tvs_disagrees_with_netlist(self):
        path = self.path / 'photoreactor_quad.kicad_pcb'
        tree = parse(path.read_text())
        ground = next((n for n in tree if isinstance(n,list) and n[0]=='net' and len(n)>2 and n[2]=='"GND"'),None)
        for fp in tree:
            if not isinstance(fp, list) or fp[0] != 'footprint': continue
            if not any(isinstance(t,list) and (t[:3]==['fp_text','reference','"D_TVS"'] or t[:3]==['property','"Reference"','"D_TVS"']) for t in fp):continue
            pad = next(p for p in fp if isinstance(p, list) and p[0] == 'pad' and p[1].strip('"') == '1')
            child(pad,'net')[1:] = ground[1:] if ground else ['"GND"']
        path.write_text(dump(tree))
        self.check_script('validate_pcb.py', 'quad', fail=True,
                          message='D_TVS pad 1 net GND differs from source netlist +12V')


if __name__ == '__main__':
    unittest.main()
