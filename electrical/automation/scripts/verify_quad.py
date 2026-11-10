from project_paths import source_path
#!/usr/bin/env python3
"""Connectivity checks for the current four-reactor controller against design intent."""
import re, sys

def tokenize(s): return re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', s)
def parse(tk, i=0):
    out = []
    while i < len(tk):
        t = tk[i]
        if t == '(':  sub, i = parse(tk, i + 1); out.append(sub)
        elif t == ')': return out, i + 1
        else: out.append(t[1:-1] if t.startswith('"') else t); i += 1
    return out, i
def find(n, k): return [x for x in n if isinstance(x, list) and x and x[0] == k]

root, _ = parse(tokenize(open(source_path('photoreactor_quad.net')).read())); root = root[0]
netmap = {}
for n in find(find(root, 'nets')[0], 'net'):
    nodes = find(n, 'node')
    if len(nodes) == 1 and any('no_connect' in f[1] for f in find(nodes[0], 'pintype')):
        continue  # KiCad explicitly marks deliberately unused pins.
    netmap[find(n, 'name')[0][1]] = {(find(nd, 'ref')[0][1], find(nd, 'pin')[0][1])
                                     for nd in find(n, 'node')}
values = {find(c, 'ref')[0][1]: find(c, 'value')[0][1] for c in find(find(root, 'components')[0], 'comp')}
pinnet = {nd: nm for nm, nodes in netmap.items() for nd in nodes}

PIN_TO_GP = {1:0, 2:1, 4:2, 5:3, 6:4, 7:5, 9:6, 10:7, 11:8, 12:9, 14:10, 15:11,
             16:12, 17:13, 19:14, 20:15, 21:16, 22:17, 24:18, 25:19, 26:20,
             27:21, 29:22, 31:26, 32:27, 34:28}

fails = []
def check(cond, msg):
    if cond: print(f'  ok   {msg}')
    else: fails.append(msg); print(f'  FAIL {msg}')

def gp_on(net):
    return [PIN_TO_GP[int(p)] for r, p in netmap.get(net, ()) if r == 'J_PICO' and int(p) in PIN_TO_GP]

print('== LED channels (8) ==')
led_gps = []
for ch in range(1, 9):
    u = f'U_LED{ch}'
    check(pinnet.get((u, '5')) == '+12V', f'{u} VIN on +12V')
    setn, swn, ctrl = pinnet.get((u, '4')), pinnet.get((u, '1')), pinnet.get((u, '3'))
    rs = [r for r, _ in netmap[setn] if r.startswith('R') and any((r, p) in netmap['+12V'] for p in ('1', '2'))]
    check(len(rs) == 1, f'{u} one sense resistor +12V->SET')
    check(len(rs) == 1 and values.get(rs[0]) == '0R43', f'{u} current sense must be 0R43 for XINGLIGHT LED')
    ln = f'LED{ch}_LED_N'
    check(setn == f'LED{ch}_LED_P', f'{u} SET senses LED positive terminal')
    coils = [r for r, _ in netmap.get(swn, ()) if r.startswith('L')]
    check(len(coils) == 1 and
          {pinnet.get((coils[0], p)) for p in ('1', '2')} == {swn, ln},
          f'{u} inductor between LED negative terminal and SW')
    check(pinnet.get((f'D_LED{ch}', '2')) == swn and
          pinnet.get((f'D_LED{ch}', '1')) == '+12V',
          f'{u} catch diode anode SW, cathode +12V')
    check(pinnet.get((u, '2')) == 'GND', f'{u} internal switch ground reference')
    # CTRL is driven through a series R from exactly one Pico pin
    src = [n for r, _ in netmap[ctrl] if r.startswith('R') for n in
           (pinnet.get((r, '1')), pinnet.get((r, '2'))) if n != ctrl]
    gps = [g for n in src for g in gp_on(n)]
    check(len(gps) == 1, f'{u} CTRL fed from one Pico GPIO (GP{gps})')
    led_gps += gps

print('== fan channels (8) ==')
fan_gps, tach_gps = [], []
for ch in range(1, 9):
    q = f'Q_FAN{ch}'
    check(pinnet.get((q, '3')) == f'FAN{ch}_PWM' and pinnet.get((q, '2')) == 'GND', f'{q} drain on PWM, source GND')
    gate_src = [n for r, _ in netmap[f'FAN{ch}_GATE'] if r.startswith('R')
                for n in (pinnet.get((r, '1')), pinnet.get((r, '2'))) if n != f'FAN{ch}_GATE']
    g = [x for n in gate_src for x in gp_on(n)]
    check(len(g) == 1, f'{q} gate from one Pico GPIO (GP{g})')
    fan_gps += g
    t = gp_on(f'FAN{ch}_TACH_MCU')
    check(len(t) == 1, f'FAN{ch} tach on one Pico GPIO (GP{t})')
    tach_gps += t

print('== reactor cables (4) ==')
# the cable pinout must carry exactly this reactor's channels, in the agreed order
for r in range(1, 5):
    la, lb, fs, fc = 2*r-1, 2*r, 2*r-1, 2*r
    want = {1: f'LED{la}_LED_P', 2: f'LED{la}_LED_N',
            3: f'LED{lb}_LED_P', 4: f'LED{lb}_LED_N',
            5: f'FAN{fs}_TACH', 6: f'FAN{fc}_TACH', 7: 'FAN_V', 8: 'GND',
            9: f'FAN{fs}_PWM', 10: f'FAN{fc}_PWM'}
    got = {p: pinnet.get((f'J_R{r}', str(p))) for p in want}
    check(got == want, f'J_R{r} carries reactor {r}: LEDs {la},{lb}  STIR fan {fs}  COOL fan {fc}')

print('== RP2040 PWM resources ==')
pwm = led_gps + fan_gps
chans = [((g >> 1) & 7, g & 1) for g in pwm]
check(len(pwm) == 16, f'16 PWM outputs assigned (got {len(pwm)})')
check(len(set(chans)) == len(chans), 'every PWM output on its own slice channel (none locked together)')
check(not set(tach_gps) & set(pwm), 'tach inputs never share a pin with a PWM output')
check(len(set(pwm + tach_gps)) == len(pwm + tach_gps), 'no GPIO used twice')

print('== power ==')
check(pinnet.get(('Q_REV', '3')) == 'VIN_FUSED' and
      pinnet.get(('Q_REV', '2')) == '+12V' and
      pinnet.get(('Q_REV', '1')) == 'REV_GATE',
      'reverse PMOS: drain input, source protected rail, gate pulldown')
check(pinnet.get(('D_GZ', '1')) == '+12V' and
      pinnet.get(('D_GZ', '2')) == 'REV_GATE', 'gate clamp referenced to PMOS source')
check(pinnet.get(('D_TVS', '1')) == '+12V' and
      pinnet.get(('D_TVS', '2')) == 'GND', 'unidirectional TVS cathode +12V, anode GND')
check(pinnet.get(('J_PICO', '39')) == 'VSYS' and ('D_VSYS', '2') in netmap['+5V'], 'VSYS fed from +5V through D_VSYS')
check({pinnet.get(('JP_FANV', p)) for p in '123'} == {'+12V', 'FAN_V', '+5V'}, 'fan rail jumper selects 12V / 5V')
for a, b in [('+12V', '+5V'), ('+5V', '+3V3'), ('+12V', 'GND'), ('+5V', 'GND'), ('+3V3', 'GND'), ('FAN_V', 'GND')]:
    check(not (netmap.get(a, set()) & netmap.get(b, set())), f'{a} and {b} share no pin')
check(not [n for n, v in netmap.items() if len(v) < 2], 'no dangling single-pin nets')

print(f'\nRESULT: {len(fails)} failure(s)')
for f in fails: print('   -', f)
sys.exit(1 if fails else 0)
