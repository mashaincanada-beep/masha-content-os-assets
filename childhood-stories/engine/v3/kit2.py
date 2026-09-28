"""MIC Study colored-pencil doodle kit v2 (style reference: 'Mom-daughter dates').
Thin wobbly black ink lines, stick limbs, fine colored-pencil hatching, scribbled hair strands,
red smile, soft pink cheeks, pencil hearts/flowers/vines on a clean white page."""
import random, math
R=random.Random(7); _n=[0]
INK='#1f1b24'
def uid(): _n[0]+=1; return f'k{_n[0]}'
def defs(seed=4):
    return f'''<defs>
<filter id="ink" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="2" seed="{seed}"/><feDisplacementMap in="SourceGraphic" scale="3.5"/></filter>
<filter id="pencil" x="-5%" y="-5%" width="110%" height="110%">
 <feTurbulence type="fractalNoise" baseFrequency="1.2" numOctaves="1" seed="{seed+1}" result="n"/>
 <feColorMatrix in="n" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 -1.6 1.45" result="g"/>
 <feComposite in="SourceGraphic" in2="g" operator="in"/></filter>
<radialGradient id="blush"><stop offset="0" stop-color="#F48FB1" stop-opacity=".75"/><stop offset="1" stop-color="#F48FB1" stop-opacity="0"/></radialGradient>
</defs>'''
def jit(v,a=1.5): return v+R.uniform(-a,a)
def pts2d(p): return 'M'+' L'.join(f'{x:.1f} {y:.1f}' for x,y in p)
def ink(d,w=4,color=INK,fill='none'):
    return f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" filter="url(#ink)"/>'
def stick(points,w=5): return ink(pts2d(points),w)
def pencil(shape,color,bbox,angle=-40,gap=5,w=3,tint=.35,cross=False):
    """Fine colored-pencil hatching clipped to `shape` (an unstyled svg element string)."""
    cid=uid(); x0,y0,x1,y1=bbox; L=max(x1-x0,y1-y0)*1.5; cx,cy=(x0+x1)/2,(y0+y1)/2; s=''
    for ang in ([angle,angle+70] if cross else [angle]):
        a=math.radians(ang); k=-L/2
        while k<L/2:
            p=[]
            for t in (-L/2,-L/4,0,L/4,L/2):
                o=k+R.uniform(-1.2,1.2); p.append((cx+t*math.cos(a)-o*math.sin(a),cy+t*math.sin(a)+o*math.cos(a)))
            s+=pts2d(p); k+=gap+R.uniform(-1,1.5)
    return (f'<clipPath id="{cid}">{shape}</clipPath><g clip-path="url(#{cid})">'
            f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="{color}" opacity="{tint}"/>'
            f'<path d="{s}" stroke="{color}" stroke-width="{w}" stroke-linecap="round" fill="none" opacity=".9" filter="url(#pencil)"/></g>')
def shape(d,color,angle=-40,gap=5,outline=True,w=4,cross=False):
    import re
    nums=[float(n) for n in re.findall(r'-?\d+\.?\d*',d)]; xs=nums[0::2]; ys=nums[1::2]
    return pencil(f'<path d="{d}"/>',color,(min(xs)-5,min(ys)-5,max(xs)+5,max(ys)+5),angle,gap,cross=cross)+(ink(d,w) if outline else '')
def poly(p,color,**k): return shape(pts2d(p)+'Z',color,**k)
def head(cx,cy,r,skin='#FFF8F2',smile='#E53935'):
    s=pencil(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>',skin,(cx-r,cy-r,cx+r,cy+r),gap=7,tint=.6)
    s+=ink(f'M{cx+r} {cy} A{r} {r} 0 1 1 {cx+r-0.5} {cy-3}',4.5)
    e=r*0.33
    for sx in (-1,1):
        ex=cx+sx*e; ey=cy-r*0.06
        s+=f'<ellipse cx="{ex}" cy="{ey}" rx="{r*0.085+1.5:.1f}" ry="{r*0.115+2:.1f}" fill="{INK}"/><circle cx="{ex+r*0.03:.1f}" cy="{ey-r*0.05:.1f}" r="{r*0.035+0.8:.1f}" fill="#fff"/>'
        s+=ink(f'M{ex-r*0.1:.0f} {ey-r*0.26:.0f} q{r*0.1:.0f} {-r*0.07:.0f} {r*0.2:.0f} 0',2.6)
    s+=f'<circle cx="{cx-e-r*0.1}" cy="{cy+r*0.3}" r="{r*0.24}" fill="url(#blush)"/><circle cx="{cx+e+r*0.1}" cy="{cy+r*0.3}" r="{r*0.24}" fill="url(#blush)"/>'
    s+=ink(f'M{cx-r*0.34} {cy+r*0.2} Q{cx} {cy+r*0.68} {cx+r*0.34} {cy+r*0.2}',5,smile)
    return s
def hair(cx,cy,r,color,style='messy',n=70,length=1.0):
    """Scribbled pencil strands. styles: messy (short), long (falls to shoulders), bun (adds a scribbled bun)."""
    s=''
    for i in range(n):
        a=math.radians(R.uniform(195,345)); r0=r*R.uniform(0.55,0.95)
        x=cx+r0*math.cos(a); y=cy+r0*math.sin(a)*0.9
        if style=='long':
            side=-1 if math.cos(a)<0 else 1
            x2=cx+side*r*R.uniform(0.9,1.25); y2=cy+r*R.uniform(0.6,1.9)*length
            s+=f'M{x:.0f} {y:.0f} Q{cx+side*r*1.15:.0f} {cy-r*0.2:.0f} {x2:.0f} {y2:.0f}'
        else:
            x2=cx+(r+R.uniform(4,22))*math.cos(a); y2=cy+(r+R.uniform(4,22))*math.sin(a)
            s+=f'M{x:.0f} {y:.0f} Q{(x+x2)/2+R.uniform(-8,8):.0f} {(y+y2)/2+R.uniform(-8,8):.0f} {x2:.0f} {y2:.0f}'
    # fringe arcs over the forehead
    for i in range(18):
        x=cx-r*0.9+i*r*0.1; s+=f'M{x:.0f} {cy-r*0.95+abs(i-9)*2:.0f} Q{x+8:.0f} {cy-r*0.55:.0f} {x+R.uniform(-4,14):.0f} {cy-r*0.35+R.uniform(-6,6):.0f}'
    out=f'<path d="{s}" stroke="{color}" stroke-width="3.2" fill="none" stroke-linecap="round" opacity=".95"/>'
    if style=='bun':
        b=''.join(f'M{cx+R.uniform(-30,30):.0f} {cy-r-R.uniform(0,50):.0f} q{R.uniform(-25,25):.0f} {R.uniform(-25,25):.0f} {R.uniform(-30,30):.0f} {R.uniform(-20,20):.0f}' for _ in range(40))
        out+=f'<path d="{b}" stroke="{color}" stroke-width="3.2" fill="none" stroke-linecap="round"/>'
    return out
def heart(cx,cy,s,color='#E91E63',fill=True):
    d=f'M{cx} {cy+s*0.9} C{cx-s*1.5} {cy-s*0.1} {cx-s*0.7} {cy-s*1.2} {cx} {cy-s*0.35} C{cx+s*0.7} {cy-s*1.2} {cx+s*1.5} {cy-s*0.1} {cx} {cy+s*0.9}Z'
    return (pencil(f'<path d="{d}"/>',color,(cx-s*1.5,cy-s*1.2,cx+s*1.5,cy+s),gap=6,tint=.15) if fill else '')+ink(d,5,color)
def flower(x,y,r=13,color='#F06292',center='#FFCA28'):
    s=''.join(f'<circle cx="{x+r*math.cos(math.radians(a)):.0f}" cy="{y+r*math.sin(math.radians(a)):.0f}" r="{r*0.62:.0f}" fill="{color}" opacity=".78" stroke="#AD1457" stroke-width="2.6" stroke-opacity=".8" filter="url(#ink)"/>' for a in range(0,360,72))
    return s+f'<circle cx="{x}" cy="{y}" r="{r*0.38:.0f}" fill="{center}"/>'
def leaf(x,y,s=16,ang=0,color='#7CB342'):
    return f'<path d="M{x} {y} q{s} {-s*0.9} {s*2} 0 q{-s} {s*0.9} {-s*2} 0z" fill="{color}" opacity=".8" stroke="#558B2F" stroke-width="2.4" transform="rotate({ang} {x} {y})" filter="url(#pencil)"/>'
def bush(x,y,w,h,flowers=6,fcolor='#F06292'):
    s=''
    for i in range(int(w*h/900)): s+=leaf(x+R.uniform(0,w),y+R.uniform(0,h),R.uniform(10,17),R.uniform(0,360))
    for i in range(flowers): s+=flower(x+R.uniform(10,w-10),y+R.uniform(5,h-10),R.uniform(10,14),fcolor)
    return s
def vine(x,y0,y1,fcolor='#F48FB1'):
    s=ink(f'M{x} {y0} C{x+30} {y0+(y1-y0)*0.3} {x-30} {y0+(y1-y0)*0.6} {x+10} {y1}',4,'#558B2F')
    y=y0
    while y<y1:
        s+=leaf(x+R.uniform(-20,10),y,R.uniform(10,15),R.uniform(-60,60)); 
        if R.random()<0.45: s+=flower(x+R.uniform(-15,25),y+8,R.uniform(9,12),fcolor)
        y+=R.uniform(22,34)
    return s
def star(cx,cy,r,color='#FBC02D'):
    p=[(cx+(r if i%2==0 else r*0.45)*math.cos(math.radians(-90+i*36)),cy+(r if i%2==0 else r*0.45)*math.sin(math.radians(-90+i*36))) for i in range(10)]
    return poly(p,color,gap=5,w=5)
def sneaker(x,y,w=70,color='#FFFFFF',accent='#90A4AE',flip=False):
    sx=-1 if flip else 1
    d=f'M{x} {y} q{sx*w*0.1} {-w*0.35} {sx*w*0.45} {-w*0.35} q{sx*w*0.25} 0 {sx*w*0.55} {w*0.25} l0 {w*0.1} l{-sx*w} 0z'
    return shape(d,color if color!='#FFFFFF' else '#ECEFF1',gap=6)+ink(f'M{x} {y-3} l{sx*w} 0',3,accent)
def font_css(b):
    F='node_modules/@fontsource/'
    fs=[('Architects Daughter',F+'architects-daughter/files/architects-daughter-latin-400-normal.woff2'),('Gochi Hand',F+'gochi-hand/files/gochi-hand-latin-400-normal.woff2')]
    return ''.join("@font-face{font-family:'%s';src:url(data:font/woff2;base64,%s) format('woff2')}"%(n,b(p)) for n,p in fs)

# ---- v2 refinements: paper texture, ground with grass, detailed sneakers, title underline ----
def paper_filter():
    return ('<filter id="paper" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="3" seed="11"/>'
            '<feColorMatrix type="matrix" values="0 0 0 0 0.55 0 0 0 0 0.47 0 0 0 0 0.38 0 0 0 0.09 0"/></filter>'
            '<filter id="fibers"><feTurbulence type="fractalNoise" baseFrequency="0.012 0.25" numOctaves="2" seed="5"/>'
            '<feColorMatrix type="matrix" values="0 0 0 0 0.6 0 0 0 0 0.52 0 0 0 0 0.42 0 0 0 0.05 0"/></filter>')
def paper(w,h,color='#FFF8EC'):
    """Warm off-white page with subtle paper grain and fibres (add paper_filter() inside <defs>)."""
    return f'<rect width="{w}" height="{h}" fill="{color}"/><rect width="{w}" height="{h}" filter="url(#paper)"/><rect width="{w}" height="{h}" filter="url(#fibers)"/>'
def tuft(x,y,s=14,color='#7CB342'):
    return f'<path d="M{x-s*0.6:.0f} {y} q{s*0.2:.0f} {-s:.0f} {s*0.35:.0f} {-s*1.3:.0f} M{x:.0f} {y} q0 {-s*1.2:.0f} {s*0.1:.0f} {-s*1.6:.0f} M{x+s*0.6:.0f} {y} q{-s*0.1:.0f} {-s:.0f} {-s*0.3:.0f} {-s*1.2:.0f}" stroke="{color}" stroke-width="3" fill="none" stroke-linecap="round" filter="url(#pencil)"/>'
def ground(x0,x1,y,depth=30,color='#EFE3CF',petals='#F8BBD0',tint=.22):
    """Soft pencil path the characters stand on, with grass tufts and fallen petals."""
    d=f'M{x0} {y} Q{(x0+x1)/2} {y-10} {x1} {y} L{x1} {y+depth} Q{(x0+x1)/2} {y+depth+8} {x0} {y+depth}Z'
    s=pencil(f'<path d="{d}"/>',color,(x0,y-12,x1,y+depth+10),angle=-8,gap=8,tint=tint)
    s+=ink(f'M{x0} {y} Q{(x0+x1)/2} {y-10} {x1} {y}',2.5,'#D7C4B0')
    for i in range(12): s+=f'<ellipse cx="{R.uniform(x0+20,x1-20):.0f}" cy="{R.uniform(y+6,y+depth-4):.0f}" rx="{R.uniform(4,7):.0f}" ry="{R.uniform(2.5,4):.0f}" fill="{petals}" opacity=".85" transform="rotate({R.uniform(0,180):.0f})" transform-origin="center" filter="url(#pencil)"/>'
    for i in range(14): s+=tuft(R.uniform(x0+10,x1-10),y+R.uniform(-2,4),R.uniform(10,16))
    return s
def sneaker2(x,y,w=100,color='#ECEFF1',sole='#FFFFFF',lace='#90A4AE',flip=False):
    """Sneaker with sole band, toe cap and criss-cross laces. (x,y) = back of the sole."""
    k=-1 if flip else 1
    up=f'M{x} {y-8} q{k*w*0.05:.0f} {-w*0.36:.0f} {k*w*0.42:.0f} {-w*0.38:.0f} q{k*w*0.3:.0f} {w*0.02:.0f} {k*w*0.58:.0f} {w*0.3:.0f} l0 {w*0.08:.0f}z'
    s=shape(up,color,gap=5)
    s+=shape(f'M{x-k*3} {y-10} l{k*(w+4)} 0 l0 12 q{-k*w*0.5:.0f} 4 {-k*(w+4)} 0z',sole,gap=7,w=3.5)
    lx=x+k*w*0.3
    for i in range(3): s+=ink(f'M{lx+k*i*12:.0f} {y-w*0.3+i*6:.0f} l{k*12} -8 M{lx+k*i*12:.0f} {y-w*0.3+i*6-8:.0f} l{k*12} 8',2,lace)
    return s
def underline(x,y,w,color='#FFD54F',h=18):
    """Crayon highlighter swipe to sit under a title."""
    d=f'M{x} {y} q{w*0.25:.0f} {-h*0.4:.0f} {w*0.5:.0f} {-h*0.1:.0f} t{w*0.5:.0f} {-h*0.1:.0f}'
    return f'<path d="{d}" stroke="{color}" stroke-width="{h}" stroke-linecap="round" fill="none" opacity=".6" filter="url(#pencil)"/>'
