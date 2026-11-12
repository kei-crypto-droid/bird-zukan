import sys; sys.path.insert(0,'.')
from PIL import Image
from sprites import SPR
ORDER=['hirenjaku','oowashi','miyamahoojiro','benimashiko','misosazai',
       'kibitaki','akashobin','akagera','magamo','kawasemi']
S=5
def sprite(name):
    pal,txt=SPR[name]
    rows=txt.strip('\n').split('\n')
    w=max(len(r) for r in rows); h=len(rows)
    im=Image.new('RGBA',(w*S,h*S),(0,0,0,0))
    for y,r in enumerate(rows):
        for x,c in enumerate(r):
            if c=='.': continue
            col=pal[c]; rgb=tuple(int(col[i:i+2],16) for i in (1,3,5))
            im.paste(rgb+(255,),(x*S,y*S,x*S+S,y*S+S))
    return im
W,H=800,430; CW,BASE=160,[162,382]
top,bot=(200,200,200),(105,105,105)
bg=Image.new('RGB',(W,H))
for y in range(H):
    t=y/(H-1); c=tuple(round(top[i]+(bot[i]-top[i])*t) for i in range(3))
    bg.paste(c,(0,y,W,y+1))
sprites=[sprite(n) for n in ORDER]
frames=[]
for f in range(10):
    fr=bg.copy()
    for k,sp in enumerate(sprites):
        col,row=k%5,k//5
        x=col*CW+(CW-sp.width)//2
        y=BASE[row]-sp.height-(5 if k==f else 0)
        fr.paste(sp,(x,y),sp)
    frames.append(fr)
frames[0].save('preview.png')
frames[0].resize((1600,860),Image.NEAREST).save('preview2x.png')
pal=frames[0].quantize(colors=256,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
pf=[f.quantize(palette=pal,dither=Image.Dither.NONE) for f in frames]
pf[0].save('yacho10.gif',save_all=True,append_images=pf[1:],duration=80,loop=0,optimize=False)
print('ok')
