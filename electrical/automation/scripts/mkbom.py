import re, collections, csv, sys, os
from jlc_parts import lookup
from project_paths import source_path, output_dir, PCB_ROOT
DESIGN = sys.argv[1] if len(sys.argv)>1 else 'quad'
if DESIGN not in ('quad', 'led'):
    raise SystemExit('Choose quad or led; legacy projects are not included.')

def tokenize(s):
    return re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', s)

def parse(tokens, i=0):
    out=[]
    while i < len(tokens):
        t=tokens[i]
        if t=='(':
            sub,i = parse(tokens,i+1); out.append(sub)
        elif t==')':
            return out,i+1
        else:
            out.append(t[1:-1] if t.startswith('"') else t); i+=1
    return out,i

def find(node,key):
    return [x for x in node if isinstance(x,list) and x and x[0]==key]

tree,_ = parse(tokenize(open(source_path(f'photoreactor_{DESIGN}.net')).read()))
root = tree[0]
comps = find(find(root,'components')[0],'comp')
rows=[]
for c in comps:
    ref = find(c,'ref')[0][1]
    val = find(c,'value')[0][1] if len(find(c,'value')[0])>1 else ''
    fpn = find(c,'footprint'); fp = fpn[0][1] if fpn and len(fpn[0])>1 else ''
    mpn=''
    fl = find(c,'fields')
    if fl:
        for f in find(fl[0],'field'):
            nm = find(f,'name')
            if nm and nm[0][1]=='MPN' and len(f)>2: mpn=f[2]
    rows.append((ref,val,fp,mpn))

nets = find(find(root,'nets')[0],'net')
print(f"COMPONENTS: {len(rows)}   NETS: {len(nets)}")
assert len(rows)==len(set(r[0] for r in rows)), "DUPLICATE REFDES!"

# The two current designs use identical population for every built board.
def populate_of(refs):
    return 'ALWAYS'

# Assembly split, decided by what the FOOTPRINT actually is, not by its name.
# A footprint with any thru_hole pad goes to hand assembly (JLC bills THT
# separately and often won't take it on standard assembly); everything else is
# machine-placed. Name matching got this wrong three times -- most importantly
# it put the 40-pin Pico socket on the SMT list because the custom footprint's
# name didn't contain "PinSocket".
FPDIRS = (os.environ.get('KICAD_FOOTPRINT_DIR', '/usr/share/kicad/footprints'), str(PCB_ROOT/'libraries/footprints'))
def _fp_text(fpname):
    lib, name = fpname.split(':')
    for d in FPDIRS:
        path = os.path.join(d, lib + '.pretty', name + '.kicad_mod')
        if os.path.exists(path):
            return open(path).read()
    raise SystemExit(f'missing footprint: {fpname}')

# Explicit overrides: a deliberate choice, not a guess. Put a ref here to force
# it to hand assembly even though it is SMD -- e.g. a part you want to select
# or swap after the boards come back.
FORCE_HAND = set()

def assembly_of(fpname, refs):
    if all(r == 'TP_TS' for r in refs): return 'MECH'
    if 'MountingHole' in fpname or 'TestPoint' in fpname:
        return 'MECH'
    if any(r in FORCE_HAND for r in refs):
        return 'HAND'
    return 'HAND' if 'thru_hole' in _fp_text(fpname) else 'JLC-SMT'
g=collections.defaultdict(list)
for ref,val,fp,mpn in rows:
    g[(assembly_of(fp, [ref]),val,fp,mpn)].append(ref)

with open(output_dir(DESIGN)/f'BOM_{DESIGN}.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['Populate','Assembly','Qty','Refs','Value','MPN','LCSC','JLC type','Stock@lookup','Note','Footprint'])
    for (side,val,fp,mpn),refs in sorted(g.items(), key=lambda x:(x[0][0],-len(x[1]))):
        lc,typ,stk,note = lookup(val, mpn, fp)
        w.writerow([populate_of(refs),side,len(refs),' '.join(sorted(refs)),val,mpn,lc,typ,stk,note,fp])

cnt=collections.Counter(k[0] for k in g for _ in g[k])
print("placements by assembly:", dict(cnt))
print(f"unique line items: {len(g)}")
for (side,val,fp,mpn),refs in sorted(g.items(), key=lambda x:(x[0][0],-len(x[1]))):
    if side!='MECH':
        print(f"  [{side:<7}] {len(refs):>2}x {val:<20} {mpn:<20} {fp.split(':')[-1][:30]}")
