"""Reject wiring defects across both cables; work only on disposable netlists."""
from pathlib import Path
from project_paths import source_path
import shutil
import tempfile
import unittest
from test_regressions import parse,dump,child
from verify_paired import verify

class PairedWiring(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        for d in ('quad','led'):
            shutil.copy2(source_path(f'photoreactor_{d}.net'),self.root)
    def move(self,d,ref,pin,to):
        path=self.root/f'photoreactor_{d}.net';t=parse(path.read_text(encoding='utf-8'));nets=child(t,'nets')[1:]
        target=next(n for n in nets if child(n,'name')[1].strip('"')==to)
        for net in nets:
            for n in net[:]:
                if isinstance(n,list) and n[0]=='node' and child(n,'ref')[1].strip('"')==ref and child(n,'pin')[1].strip('"')==pin:
                    net.remove(n);target.append(n);path.write_text(dump(t),encoding='utf-8');return
        self.fail('Pin not found')
    def test_baseline(self):self.assertEqual(verify(self.root),[])
    def test_grounded_led_return(self):
        self.move('led','D1','2','GND');self.assertTrue(verify(self.root))
    def test_grounded_unknown_thermal_pad(self):
        self.move('led','D1','3','GND');self.assertTrue(verify(self.root))
    def test_cooling_fan_on_stir_channel(self):
        self.move('led','J2','6','LOCAL_PWM');self.assertTrue(verify(self.root))
    def test_swapped_link_power(self):
        self.move('led','J2','3','GND')
        self.move('led','J2','4','FAN_5V');self.assertTrue(verify(self.root))
    def test_reversed_led(self):
        self.move('led','D1','1','LOCAL_LED_N')
        self.move('led','D1','2','LOCAL_LED_P');self.assertTrue(verify(self.root))
    def test_fan_tach_pwm_swapped(self):
        self.move('led','J3','3','LOCAL_PWM')
        self.move('led','J3','4','LOCAL_TACH');self.assertTrue(verify(self.root))

    def test_led_slots_not_swapped(self):
        for pin,net in [('1','LOCAL_LED_P'),('2','LOCAL_LED_N')]:
            self.move('led','J2',pin,net)
        self.assertTrue(verify(self.root))
    def test_tach_slots_not_swapped(self):
        self.move('led','J2','5','LOCAL_TACH')
        self.assertTrue(verify(self.root))

    def test_incorrect_straight_six_pin_cable(self):
        self.assertTrue(verify(self.root,{i:i for i in range(1,7)}))
    def test_missing_pwm_wire(self):
        self.assertTrue(verify(self.root,{1:1,2:2,3:7,4:8,5:5}))

if __name__=='__main__':unittest.main()
