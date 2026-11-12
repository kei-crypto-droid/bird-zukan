import sys; sys.path.insert(0,'.')
from PIL import Image
from sprites import SPR
ORDER=['kawasemi','akashobin','kibitaki','akagera','miyamahoojiro','hirenjaku','oowashi','misosazai','benimashiko','magamo']
S=5
def sprite(name):
    pal,txt=SPR[name]
    rows=[r for r in txt.strip('\n').split('\n')]
    w=max(len(r) for r in rows); h=len(rows)
    im=Image.new('RGBA',(w*S,h*S),(0,0,0,0))
    for y,r in enumerate(rows):
        for x,c in enumerate(r):
            if c=='.' : continue
            col=pal[c]; rgb=tuple(int(col[i:i+2],16) for i in (1,3,5))
            for dy in range(S):
                for dx in range(S): im.putpixel((x*S+dx,y*S+dy),rgb+(255,))
    return im
W,H=800,430; CW,BASE=160,[160,380]
sprites=[sprite(n) for n in ORDER]
frames=[]
for f in range(10):
    fr=Image.new('RGB',(W,H),(0,0,0))
    for k,sp in enumerate(sprites):
        col,row=k%5,k//5
        x=col*CW+(CW-sp.width)//2
        y=BASE[row]-sp.height-(5 if k==f else 0)
        fr.paste(sp,(x,y),sp)
    frames.append(fr)
frames[0].save('preview.png')
frames[0].resize((1600,860),Image.NEAREST).save('preview2x.png')
pf=[f.quantize(colors=255,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE) for f in frames]
pf[0].save('yacho10.gif',save_all=True,append_images=pf[1:],duration=80,loop=0,disposal=2,optimize=False)
print('ok')
