from project_paths import source_path
#!/usr/bin/env python3
"""
Geometric validation of the generated board. Checks what kicad-cli 7 can't:
  - every pad's net number is declared
  - every footprint lies inside the board outline, with margin
  - no two footprints' pad bounding boxes overlap
  - nothing intrudes into the Pico W antenna keepout
Exits non-zero on any failure.
"""
import re, sys, math, itertools, collections
from pico_geometry import antenna_cutout

DESIGN = sys.argv[1] if len(sys.argv) > 1 else 'quad'
if DESIGN != 'quad':
    raise SystemExit('This geometry check targets the current quad controller only.')
PCB = 'photoreactor_quad.kicad_pcb'
BOARD_W, BOARD_H = 130.0, 100.0
KEEPOUT = antenna_cutout(20.0, 28.0)
EDGE_MARGIN = 0.5
# Check individual pads, including the Pico; its bounding box spans the hole.

TOK = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')
def parse(t):
    tk = TOK.findall(t)
    def rec(i):
        o=[]
        while i < len(tk):
            x=tk[i]
            if x=='(': s,i=rec(i+1); o.append(s)
            elif x==')': return o,i+1
            else: o.append(x); i+=1
        return o,i
    return rec(0)[0][0]
def val(t): return t[1:-1] if isinstance(t,str) and t.startswith('"') else t
def kids(n,k): return [x for x in n if isinstance(x,list) and x and val(x[0])==k]
def kid(n,k):
    r=kids(n,k); return r[0] if r else None

b = parse(open(source_path(PCB)).read())
declared = {int(val(n[1])) for n in kids(b,'net')}
net_names = {int(val(n[1])): val(n[2]) for n in kids(b, 'net')}
netlist = parse(open(source_path(f'photoreactor_{DESIGN}.net')).read())
expected_pads = {}
expected_nc = {}
for net in kids(kid(netlist, 'nets'), 'net'):
    for node in kids(net, 'node'):
        pt = kid(node, 'pintype')
        if len(kids(net, 'node')) == 1 and pt and 'no_connect' in val(pt[1]):
            expected_nc[(val(kid(node, 'ref')[1]), val(kid(node, 'pin')[1]))] = val(kid(net, 'name')[1])
            continue
        expected_pads[(val(kid(node, 'ref')[1]), val(kid(node, 'pin')[1]))] = val(kid(net, 'name')[1])
seen_pads = set()

fails = []
boxes  = {}
pad_boxes = []
for fp in kids(b,'footprint'):
    at = kid(fp,'at')
    fx, fy = float(val(at[1])), float(val(at[2]))
    frot = float(val(at[3])) if len(at)>3 else 0.0
    ref = next((val(t[2]) for t in kids(fp,'property') if val(t[1])=='Reference'), None) or next((val(t[2]) for t in kids(fp,'fp_text') if val(t[1])=='reference'), '?')
    pts=[]
    for pad in kids(fp,'pad'):
        pat = kid(pad,'at')
        px, py = float(val(pat[1])), float(val(pat[2]))
        sz = kid(pad,'size')
        sw, sh = float(val(sz[1])), float(val(sz[2]))
        # footprint rotation rotates pad positions about the footprint origin
        a = math.radians(-frot)
        rx = px*math.cos(a) - py*math.sin(a)
        ry = px*math.sin(a) + py*math.cos(a)
        # conservative: use the larger pad dimension in both axes
        pa=math.radians(float(val(pat[3])) if len(pat)>3 else frot)
        hx=(abs(sw*math.cos(pa))+abs(sh*math.sin(pa)))/2
        hy=(abs(sw*math.sin(pa))+abs(sh*math.cos(pa)))/2
        pts.append((fx+rx-hx, fy+ry-hy, fx+rx+hx, fy+ry+hy))
        pad_boxes.append((ref, val(pad[1]), pts[-1]))
        nt = kid(pad,'net')
        key = (ref, val(pad[1]))
        seen_pads.add(key)
        actual = (val(nt[1]) if len(nt)==2 else net_names.get(int(val(nt[1])))) if nt else None
        if actual != expected_pads.get(key) and not (key in expected_nc and actual == expected_nc[key]):
            fails.append(f'{ref} pad {key[1]} net {actual} differs from source netlist {expected_pads.get(key)}')
        if nt and len(nt)>2:
            nn = int(val(nt[1]))
            if nn not in declared:
                fails.append(f'{ref} pad {val(pad[1])}: undeclared net {nn}')
    if not pts:
        continue
    boxes[ref] = (min(p[0] for p in pts), min(p[1] for p in pts),
                  max(p[2] for p in pts), max(p[3] for p in pts))

print(f'footprints with pads: {len(boxes)}   declared nets: {len(declared)}')
for ref, pin in expected_pads.keys() - seen_pads:
    fails.append(f'{ref} pin {pin} has a net but no footprint pad')

print('\n== inside board outline ==')
out = []
for ref,(x1,y1,x2,y2) in sorted(boxes.items()):
    if (x1 < EDGE_MARGIN or y1 < EDGE_MARGIN
            or x2 > BOARD_W-EDGE_MARGIN or y2 > BOARD_H-EDGE_MARGIN):
        out.append((ref, round(x1,1), round(y1,1), round(x2,1), round(y2,1)))
if out:
    for r in out[:25]:
        print(f'  OUTSIDE {r[0]:<10} bbox=({r[1]},{r[2]})-({r[3]},{r[4]})')
    if len(out)>25: print(f'  ... and {len(out)-25} more')
    fails.append(f'{len(out)} footprint(s) outside the board outline')
else:
    print('  ok  all footprints inside')

print('\n== overlaps ==')
ov=[]
for (ra,A),(rb,B) in itertools.combinations(sorted(boxes.items()),2):
    if A[0] < B[2] and B[0] < A[2] and A[1] < B[3] and B[1] < A[3]:
        ov.append((ra,rb))
if ov:
    for a,b_ in ov[:25]: print(f'  OVERLAP {a} <-> {b_}')
    if len(ov)>25: print(f'  ... and {len(ov)-25} more')
    fails.append(f'{len(ov)} footprint overlap(s)')
else:
    print('  ok  no overlapping footprints')

print('\n== antenna keepout ==')
kx1,ky1,kx2,ky2 = KEEPOUT
intr=[f'{r}.{p}' for r,p,(x1,y1,x2,y2) in pad_boxes
      if x1<kx2 and kx1<x2 and y1<ky2 and ky1<y2]
if intr:
    print('  INTRUDES:', intr); fails.append(f'{len(intr)} part(s) in antenna keepout')
else:
    print('  ok  keepout clear')

# Inspect actual Edge.Cuts loops as well, so a misplaced generated cutout
# cannot pass by merely disagreeing with the expected antenna rectangle.
print('\n== internal cutouts ==')
edges = []
for shape in kids(b, 'gr_line'):
    if val(kid(shape, 'layer')[1]) != 'Edge.Cuts': continue
    edges.append(tuple(tuple(round(float(val(v)), 5) for v in kid(shape, k)[1:3])
                       for k in ('start', 'end')))
remaining = set(range(len(edges)))
cutouts = []
while remaining:
    pending = [remaining.pop()]; component = []
    while pending:
        i = pending.pop(); component.append(i)
        linked = {j for j in remaining if set(edges[i]) & set(edges[j])}
        remaining -= linked; pending.extend(linked)
    points = [p for i in component for p in edges[i]]
    counts = collections.Counter(points)
    if any(n != 2 for n in counts.values()):
        fails.append('open or branching Edge.Cuts loop'); continue
    xs, ys = zip(*points)
    rect = (min(xs), min(ys), max(xs), max(ys))
    if rect == (0.0, 0.0, BOARD_W, BOARD_H): continue
    # Generated boards use rectangular openings. Reject unknown geometry
    # rather than silently applying a rectangle approximation to an arbitrary cut.
    if len(component) != 4 or len(set(xs)) != 2 or len(set(ys)) != 2:
        fails.append('unsupported non-rectangular internal cutout'); continue
    cutouts.append(rect)
    x1,y1,x2,y2 = rect
    for ref,p,(px1,py1,px2,py2) in pad_boxes:
        if px1 < x2+EDGE_MARGIN and x1-EDGE_MARGIN < px2 and py1 < y2+EDGE_MARGIN and y1-EDGE_MARGIN < py2:
            fails.append(f'{ref} pad {p} intersects cutout or its {EDGE_MARGIN} mm edge clearance')
expected = [] if DESIGN == 'rxb' else [KEEPOUT]
if sorted(cutouts) != sorted(expected):
    fails.append(f'actual cutouts {cutouts} differ from expected {expected}')
print(f'  checked {len(cutouts)} cutout(s) against every pad (no socket exemption)')

print(f'\nRESULT: {len(fails)} failure(s)')
for f in fails: print('   -', f)
sys.exit(1 if fails else 0)
