"""End-to-end controller -> first identical board -> second board checks.

Checks independent electrical pin partitions, not labels alone. Callable by tests.
"""
from pathlib import Path
import re
from project_paths import source_path

def parse(text):
    ts=iter(re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+',text))
    def node():
        result=[]
        for t in ts:
            if t==')':return result
            result.append(node() if t=='(' else t.strip('"'))
        return result
    return node()[0]
def kids(n,k):return [x for x in n if isinstance(x,list) and x[0]==k]
def kid(n,k):return next(iter(kids(n,k)),None)
def read(path):
    t=parse(path.read_text(encoding='utf-8'));mapping={};parts={}
    for c in kids(kid(t,'components'),'comp'):
        parts[kid(c,'ref')[1]]=c
    for n in kids(kid(t,'nets'),'net'):
        for p in kids(n,'node'):mapping[kid(p,'ref')[1],kid(p,'pin')[1]]=kid(n,'name')[1]
    return mapping,parts

LINK_MAP = {1:1, 2:2, 3:7, 4:8, 5:5, 6:9}

def verify(root=None, link_map=None):
    root_path = (lambda n: source_path(n)) if root is None else (lambda n: root/n)
    link_map = LINK_MAP if link_map is None else link_map
    q,qp=read(root_path('photoreactor_quad.net'));a,ap=read(root_path('photoreactor_led.net'));b,bp=read(root_path('photoreactor_led.net'))
    errors=[]
    def check(condition,description):
        if not condition:errors.append(description)
    for reactor in range(1,5):
        parent={}
        def find(x):
            parent.setdefault(x,x)
            if parent[x]!=x:parent[x]=find(parent[x])
            return parent[x]
        def union(x,y):parent[find(x)]=find(y)
        def n(board,pin):return (board,{'Q':q,'A':a,'B':b}[board].get(pin,('MISSING',pin)))
        for pin in range(1,11):union(n('Q',(f'J_R{reactor}',str(pin))),n('A',('J1',str(pin))))
        for source,dest in link_map.items():union(n('A',('J2',str(source))),n('B',('J1',str(dest))))
        independent=['GND','FAN_V']+[f'{kind}{ch}_{suffix}' for ch in (reactor*2-1,reactor*2) for kind,suffix in [('LED','LED_N'),('LED','LED_P'),('FAN','TACH'),('FAN','PWM')]]
        check(len({find(('Q',x)) for x in independent})==10,f'R{reactor} channels must remain independent')
        for board,ch in [('A',reactor*2-1),('B',reactor*2)]:
            for pin,net in [('1',f'LED{ch}_LED_P'),('2',f'LED{ch}_LED_N')]:
                check(find(n(board,('D1',pin)))==find(('Q',net)),f'R{reactor} {board} LED pin {pin} must reach {net}')
            check(find(n(board,('D1','3'))) not in {find(('Q',x)) for x in independent}, f'R{reactor} {board} LED thermal island must be separate from all cable nets')
            for pin,net in [('1','GND'),('2','FAN_V'),('3',f'FAN{ch}_TACH'),('4',f'FAN{ch}_PWM')]:
                check(find(n(board,('J3',pin)))==find(('Q',net)),f'R{reactor} {board} fan pin {pin} must reach {net}')
            distinct=['GND','FAN_V',f'LED{ch}_LED_N',f'LED{ch}_LED_P',f'FAN{ch}_TACH',f'FAN{ch}_PWM']
            check(len({find(('Q',x)) for x in distinct})==len(distinct),f'R{reactor} {board} power/LED/control short')
            mapping=a if board=='A' else b
            for ref in ('C1','C2'):
                check(find(n(board,(ref,'1')))==find(('Q','FAN_V')) and find(n(board,(ref,'2')))==find(('Q','GND')),f'{board} {ref} fan bypass polarity')
            check(find(n(board,('R1','1')))==find(('Q','FAN_V')) and find(n(board,('R1','2')))==find(('Q',f'FAN{ch}_PWM')),f'{board} PWM pull-up mapping')
    check({pin for ref,pin in a if ref=='J2'}==set('123456'),'OUT must have exactly six connected contacts')
    check(kid(ap['J2'],'footprint')[1]=='Connector_JST:JST_PH_S6B-PH-SM4-TB_1x06-1MP_P2.00mm_Horizontal','Six-pin OUT footprint')
    for label,parts,count in [('A',ap,12),('B',bp,12)]:
        check(len(parts)==count,f'{label} expected {count} board items')
        check(kid(parts['D1'],'value')[1]=='XL-HD6070UGC-A2-BD',f'{label} correct green LED')
        check(kid(parts['D1'],'footprint')[1]=='photoreactor:LED_XINGLIGHT_XL_HD6070UGC_A2_BD',f'{label} LED thermal footprint')
    return errors

if __name__=='__main__':
    errors=verify()
    for e in errors:print('FAIL',e)
    print(f'Paired boards: all four reactor paths checked; {len(errors)} failure(s).')
    raise SystemExit(bool(errors))
