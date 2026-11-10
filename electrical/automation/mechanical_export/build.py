"""Build named mechanical STEP assemblies without editing manufacturing CAD.

Run with Python 3.12 and cadquery-ocp-novtk in deps_stable (local tool dependency).
Sources: native footprints, existing KiCad board STEP exports, manufacturer drawings.
"""
from pathlib import Path
import sys, math, json, hashlib, os

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE / 'deps_stable'))
sys.path.insert(0, str(ROOT / 'electrical/automation/scripts'))
from verify_paired import parse, kids, kid
from OCP.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax1, gp_Ax2, gp_Trsf, gp_GTrsf
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeSphere
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Common
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_GTransform
from OCP.TopoDS import TopoDS_Compound, TopoDS
from OCP.BRep import BRep_Builder, BRep_Tool
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
from OCP.STEPControl import STEPControl_Reader
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.IFSelect import IFSelect_RetDone
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorType
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_SOLID
from OCP.TopLoc import TopLoc_Location

_model_paths = [Path('C:/Program Files/KiCad/10.0/share/kicad/3dmodels'),
                Path('/usr/share/kicad/3dmodels'),
                Path('/usr/local/share/kicad/3dmodels')]
LIB = Path(os.environ['KICAD_3DMODEL_DIR']) if 'KICAD_3DMODEL_DIR' in os.environ else next(
    (p for p in _model_paths if p.is_dir()), _model_paths[0])
GREEN=(.12,.36,.22); WHITE=(.87,.88,.84); BLACK=(.13,.15,.17)
GOLD=(.78,.60,.20); SILVER=(.65,.68,.70); AMBER=(.93,.56,.12)

def box(x,y,z,dx,dy,dz):
    return BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),dx,dy,dz).Shape()

def cyl(x,y,z,r,h,direction=(0,0,1)):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(*direction)),r,h).Shape()

def compound(shapes):
    c=TopoDS_Compound(); b=BRep_Builder(); b.MakeCompound(c)
    for s in shapes:b.Add(c,s)
    return c

def bbox(shape):
    b=Bnd_Box();BRepBndLib.AddOptimal_s(shape,b)
    p,q=b.CornerMin(),b.CornerMax()
    return [round(v,6) for v in (p.X(),p.Y(),p.Z(),q.X(),q.Y(),q.Z())]

def load_step(path):
    assert path.exists(),path
    r=STEPControl_Reader();assert r.ReadFile(str(path))==IFSelect_RetDone,path
    assert r.TransferRoots()>0,path
    s=r.OneShape();assert not s.IsNull(),path
    return s

def move(shape,x=0,y=0,z=0,angle=0,bottom=False):
    if bottom:
        t=gp_Trsf();t.SetRotation(gp_Ax1(gp_Pnt(0,0,0),gp_Dir(1,0,0)),math.pi)
        shape=BRepBuilderAPI_Transform(shape,t,True).Shape()
    if angle:
        t=gp_Trsf();t.SetRotation(gp_Ax1(gp_Pnt(0,0,0),gp_Dir(0,0,1)),math.radians(angle))
        shape=BRepBuilderAPI_Transform(shape,t,True).Shape()
    t=gp_Trsf();t.SetTranslation(gp_Vec(x,y,z))
    return BRepBuilderAPI_Transform(shape,t,True).Shape()

def place(shape,fp,thickness):
    at=kid(fp,'at');x,y=map(float,at[1:3]);angle=float(at[3]) if len(at)>3 else 0
    bottom=kid(fp,'layer')[1]=='B.Cu'
    return move(shape,x,-y,0 if bottom else thickness,angle,bottom)

def idc():
    # JXTC drawing: 2x5 body 9.0 x (10.16+7.6) mm; height 9.6;
    # overall solder-tail span 10.2mm. Interior/key details simplified.
    s=box(-4.5,-8.88,.3,9,17.76,9.3)
    s=BRepAlgoAPI_Cut(s,box(-3.3,-7.68,2.3,6.6,15.36,8)).Shape()
    s=BRepAlgoAPI_Cut(s,box(-4.6,-2.25,2.3,1.5,4.5,8)).Shape()
    tails=[];posts=[]
    for y in (-5.08,-2.54,0,2.54,5.08):
        for sign in (-1,1):
            tails.append(box(-5.1 if sign<0 else 1.27,y-.32,0,3.83,.64,.3))
            posts.append(box(sign*1.27-.32,y-.32,2.3,.64,.64,6.3))
    return [('housing',s,BLACK),('contacts',compound(tails+posts),GOLD)]

def jst(n):
    # JST ePH page 4: SMT side-entry B=11.9/15.9, depth 8.6, height 5.5.
    # Front-side footprint body occupies y=-3.2..4.4 in PCB coordinates;
    # canonical 3D Y is reversed. Pad to the manufacturer's overall depth.
    width=(n-1)*2+5.9
    s=box(-width/2,-4.9,0,width,8.6,5.5)
    s=BRepAlgoAPI_Cut(s,box(-width/2+.8,-5.0,.8,width-1.6,7.8,3.8)).Shape()
    posts=[]
    for i in range(n):
        x=-(n-1)+i*2
        posts.append(box(x-.25,-3.65,1.7,.5,6.5,.5))
    return [('housing_envelope',s,WHITE),('contacts',compound(posts),SILVER)]

def led():
    # XINGLIGHT drawing page 8. Optical surface is a simplified hemisphere.
    body=BRepAlgoAPI_Common(cyl(0,0,0,4,2.75),box(-3.65,-4,0,7.3,8,2.75)).Shape()
    dome=BRepAlgoAPI_Common(BRepPrimAPI_MakeSphere(gp_Pnt(0,0,2.75),2.4).Shape(),box(-3,-3,2.75,6,6,2.4)).Shape()
    leads=compound([box(-7.25,-2.05,0,3.7,1.8,.3),box(3.55,.25,0,3.7,1.8,.3)])
    return [('body_envelope',body,WHITE),('optical_dome_approx',dome,(.35,.78,.35)),('terminals',leads,SILVER)]

def jack():
    # Existing PCB footprint fixes origin and direction. Wurth drawing:
    # body 9 x 14.5 x 10.7, front aperture dia 6.4; front at PCB local +13.6Y.
    s=box(-4.5,-13.6,0,9,14.5,10.7)
    s=BRepAlgoAPI_Cut(s,cyl(0,-13.7,6.4,3.2,9.3,(0,1,0))).Shape()
    pin=cyl(0,-13.6,6.4,1,8,(0,1,0))
    return [('housing_envelope',s,BLACK),('centre_pin',pin,SILVER)]

def sockets():
    # Sullins PPPC201LFBN-RC: length51.30, width2.54, height8.50, tail3.20.
    bodies=[];tails=[]
    for x in (-8.89,8.89):
        bodies.append(box(x-1.27,-25.65,0,2.54,51.3,8.5))
        for i in range(20):
            y=-24.13+i*2.54
            tails.append(box(x-.375,y-.2,-3.2,.75,.4,3.2))
    return [('socket_body_envelopes',compound(bodies),BLACK),('socket_tails',compound(tails),GOLD)]

def assembly_write(parts,path):
    doc=TDocStd_Document(TCollection_ExtendedString('BinXCAF'))
    st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main());ct=XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    root=st.NewShape();TDataStd_Name.Set_s(root,TCollection_ExtendedString(path.stem))
    for name,shape,color in parts:
        assert BRepCheck_Analyzer(shape).IsValid(),name
        label=st.AddShape(shape,False);TDataStd_Name.Set_s(label,TCollection_ExtendedString(name))
        ct.SetColor(label,Quantity_Color(*color,Quantity_TOC_RGB),XCAFDoc_ColorType.XCAFDoc_ColorSurf)
        component=st.AddComponent(root,label,TopLoc_Location())
        TDataStd_Name.Set_s(component,TCollection_ExtendedString(name))
    st.UpdateAssemblies()
    w=STEPCAFControl_Writer();w.SetNameMode(True);w.SetColorMode(True)
    assert w.Transfer(doc);assert w.Write(str(path))==IFSelect_RetDone
    result=load_step(path);assert BRepCheck_Analyzer(result).IsValid(),path
    return result

def preview(parts,path,title,bottom=False):
    # Orthographic triangle renderer with a real z buffer. Painter sorting
    # cannot reliably draw large PCB triangles behind small components.
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    width,height=1500,1100
    view=np.array([.9,-1.25,-1.0 if bottom else 1.0]);view/=np.linalg.norm(view)
    right=np.cross(np.array([0.,0.,1.]),view);right/=np.linalg.norm(right)
    up=np.cross(view,right)
    matrix=np.stack([right,up,view])
    triangles=[];colors=[]
    for name,shape,color in parts:
        BRepMesh_IncrementalMesh(shape,.5,False,.35,True)
        e=TopExp_Explorer(shape,TopAbs_FACE)
        while e.More():
            face=TopoDS.Face_s(e.Current());loc=TopLoc_Location()
            tri=BRep_Tool.Triangulation_s(face,loc)
            if tri:
                tr=loc.Transformation()
                nodes=np.array([tri.Node(j).Transformed(tr).Coord() for j in range(1,tri.NbNodes()+1)])
                for i in range(1,tri.NbTriangles()+1):
                    indices=np.asarray(tri.Triangle(i).Get())-1
                    vertices=nodes[indices]
                    normal=np.cross(vertices[1]-vertices[0],vertices[2]-vertices[0]);norm=np.linalg.norm(normal)
                    if norm<1e-12:continue
                    shade=.58+.42*abs(float(np.dot(normal/norm,view)))
                    triangles.append(vertices@matrix.T)
                    colors.append(np.asarray(color)*255*shade)
            e.Next()
    points=np.concatenate(triangles);lo=points[:,:2].min(axis=0);hi=points[:,:2].max(axis=0)
    scale=min((width-150)/(hi[0]-lo[0]),(height-230)/(hi[1]-lo[1]))
    centre=(lo+hi)/2
    pixels=np.full((height,width,3),[243,245,247],dtype=np.uint8)
    depth=np.full((height,width),-np.inf)
    for t,color in zip(triangles,colors):
        t=t.copy();t[:,0]=(t[:,0]-centre[0])*scale+width/2
        t[:,1]=-(t[:,1]-centre[1])*scale+height/2+40
        x0=max(0,int(np.floor(t[:,0].min())));x1=min(width-1,int(np.ceil(t[:,0].max())))
        y0=max(130,int(np.floor(t[:,1].min())));y1=min(height-1,int(np.ceil(t[:,1].max())))
        if x1<x0 or y1<y0:continue
        a,b,c=t
        denominator=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(denominator)<1e-9:continue
        xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
        u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/denominator
        v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/denominator
        w=1-u-v;zz=u*a[2]+v*b[2]+w*c[2]
        region=depth[y0:y1+1,x0:x1+1]
        mask=(u>=-1e-8)&(v>=-1e-8)&(w>=-1e-8)&(zz>region)
        region[mask]=zz[mask];pixels[y0:y1+1,x0:x1+1][mask]=color.astype(np.uint8)
    image=Image.fromarray(pixels);draw=ImageDraw.Draw(image)
    candidates=[os.environ.get('PHOTOREACTOR_FONT',''), 'C:/Windows/Fonts/arial.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/System/Library/Fonts/Supplemental/Arial.ttf']
    font_path=next((p for p in candidates if p and Path(p).is_file()),None)
    title_font=ImageFont.truetype(font_path,32) if font_path else ImageFont.load_default(size=32)
    subtitle_font=ImageFont.truetype(font_path,23) if font_path else ImageFont.load_default(size=23)
    draw.text((50,30),title,font=title_font,fill='#182b38')
    draw.text((50,78),'Mechanical reference - simplified component geometry',font=subtitle_font,fill='#536572')
    image.save(path)

def main():
    inventory=[]
    for board,base,pn in [('controller','photoreactor_quad','SDL4-0001'),('led_board','photoreactor_led','SDL4-0002')]:
        if '--led-only' in sys.argv and board!='led_board':continue
        native=ROOT/f'electrical/designs/{board}/{base}.kicad_pcb';digest=hashlib.sha256(native.read_bytes()).hexdigest()
        tree=parse(native.read_text());thickness=float(kid(kid(tree,'general'),'thickness')[1])
        fps={next(p[2] for p in kids(f,'property') if p[1]=='Reference'):f for f in kids(tree,'footprint')}
        release_names={'controller': 'SDL4-0001_photoreactor-controller_Rev-A_2026-10-08', 'led_board': 'SDL4-0002_photoreactor-led_Rev-A_2026-10-08'}
        release_name=release_names[board]
        out=ROOT/f'electrical/outputs/{board}/{release_name}/step';out.mkdir(exist_ok=True)
        bare=load_step(out/f'{release_name}_board-only.step')
        # Bare KiCad export omits outer copper thickness. Normalize the board
        # envelope to its nominal finished thickness for enclosure fit checks.
        bb=bbox(bare);tr=gp_GTrsf();tr.SetValue(3,3,thickness/(bb[5]-bb[2]))
        bare=BRepBuilderAPI_GTransform(bare,tr,True).Shape()
        parts=[('PCB_nominal_finished_thickness',bare,GREEN if board=='controller' else WHITE)]
        def add(ref,items):
            for label,s,color in items:parts.append((ref+'_'+label,place(s,fps[ref],thickness),color))
        if board=='controller':
            for ref in ('J_R1','J_R2','J_R3','J_R4'):add(ref,idc())
            add('J_PWR',jack());add('J_PICO',sockets())
            pico=load_step(LIB/'Module.3dshapes/RaspberryPi_Pico_H.step')
            # H model includes its 2.54mm header spacer. Rest it on 8.5mm sockets.
            add('J_PICO',[('Pico_H_KiCad_model',move(pico,z=8.5),GREEN)])
            add('C1',[('7p7mm_height_envelope',cyl(0,0,0,3.15,7.7),SILVER)])
            add('JP_FANV',[('header_and_5V_shunt_envelope',box(-2,-3.81,0,4,7.62,8.1),BLACK)])
            # Inductors are other significant enclosure-height obstacles.
            for ref in ('L1','L2','L3','L4','L5','L6','L7','L8','L9'):
                add(ref,[('envelope',box(-3,-3,0,6,6,4.5),BLACK)])
        else:
            add('D1',led());add('J1',idc());add('J2',jst(6));add('J3',jst(4))
            for ref in ('C1','C2','R1'):
                add(ref,[('envelope',box(-1,-.625,0,2,1.25,1.35 if ref.startswith('C') else .6),SILVER)])
            parts.append(('REAR_22x22_HEATSINK_CONTACT_AREA',box(16.5,-38.5,-.035,22,22,.035),GOLD))
            clearance=[('REFERENCE_ONLY_26x26_HEATSINK_RESERVED_VOLUME',box(14.5,-40.5,-6.289,26,26,6.254),AMBER)]
            assembly_write(clearance,out/f'{release_name}_heatsink-clearance.step')
            # Separate reference volume, not material fitted to the PCB.
            preview(parts+clearance,out/'heatsink-clearance-preview.png',pn+' - rear heatsink reserved volume',True)
        assembled=assembly_write(parts,out/f'{release_name}_mechanical-assembly.step')
        preview(parts,out/'mechanical-assembly-top.png',pn+' - component / LED side')
        preview(parts,out/'mechanical-assembly-bottom.png',pn+' - underside / connector side',True)
        assert hashlib.sha256(native.read_bytes()).hexdigest()==digest
        info={'part':pn,'native_sha256':digest,'nominal_board_thickness_mm':thickness,'assembly_bbox_mm':bbox(assembled),'components':[{'name':n,'bbox_mm':bbox(s)} for n,s,_ in parts]}
        (out/'mechanical-inventory.json').write_text(json.dumps(info,indent=2))
        inventory.append(info)
        print(pn,'exported',len(parts),'named shapes; native PCB unchanged',flush=True)
    (HERE/'validation.json').write_text(json.dumps(inventory,indent=2))

if __name__=='__main__':main()
