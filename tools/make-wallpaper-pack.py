#!/usr/bin/env python3
"""Original geometric pixel wallpapers; render at 480×270, then upscale 4×."""
from pathlib import Path
import math, random
from PIL import Image, ImageDraw, ImageOps
OUT=Path(__file__).resolve().parents[1]/'assets/wallpapers'
OUT.mkdir(parents=True,exist_ok=True)
W,H=480,270

def canvas(top,bottom):
    image=Image.new('RGB',(W,H));d=ImageDraw.Draw(image)
    for y in range(H):
        t=(y//3*3)/(H-1)
        c=tuple(round(a+(b-a)*t) for a,b in zip(top,bottom))
        d.line((0,y,W,y),fill=c)
    return image,d

def stars(d,seed=19):
    r=random.Random(seed)
    for _ in range(70):
        x,y=r.randrange(W),r.randrange(15,145)
        d.point((x,y),fill=r.choice(['#4a617e','#6e83a2','#34445f']))
    for x,y in [(50,39),(287,27),(438,81)]:
        d.line((x-1,y,x+1,y),fill='#8ba0c0');d.line((x,y-1,x,y+1),fill='#8ba0c0')

def moon(d,x,y,r):
    d.ellipse((x-r,y-r,x+r,y+r),fill='#a8bdd7')
    d.ellipse((x-r+5,y-r+4,x+r-5,y+r-4),fill='#b7c9df')
    d.rectangle((x+4,y-8,x+9,y-5),fill='#96accb')
    d.rectangle((x-10,y+5,x-5,y+8),fill='#96accb')

def save(image,name):
    path=OUT/name
    image.resize((1920,1080),Image.Resampling.NEAREST).save(path,optimize=True)
    print(path)

im,d=canvas((10,13,24),(33,47,72));stars(d);moon(d,365,64,17)
d.polygon([(0,173),(48,136),(82,164),(153,91),(216,162),(271,127),(335,173),(402,121),(480,180),(480,270),(0,270)],fill='#24354e')
d.polygon([(108,140),(153,91),(184,126),(159,114),(149,124),(140,119)],fill='#8196b2')
d.polygon([(0,207),(65,171),(111,195),(186,152),(251,206),(318,160),(382,200),(440,167),(480,195),(480,270),(0,270)],fill='#18263b')
d.rectangle((0,222,480,270),fill='#121e31')
r=random.Random(53)
for y in range(227,268,5):
    length=r.randrange(12,45); x=365+r.randrange(-20,20)
    d.line((x-length//2,y,x+length//2,y),fill='#435771')
for x in list(range(-4,95,14))+list(range(410,490,11)):
    top=random.Random(x).randrange(197,226)
    d.rectangle((x-1,top,x+1,270),fill='#0b1321')
    for offset in range(0,28,5):d.polygon([(x,top-10+offset),(x-7-offset//4,top+3+offset),(x+7+offset//4,top+3+offset)],fill='#0b1321')
save(im,'02-blue-hour-mountains.png')

im,d=canvas((9,12,21),(26,32,51));stars(d,31);moon(d,378,65,20)
r=random.Random(77)
for layer,color,base in [(0,'#1c2940',170),(1,'#142035',202),(2,'#0d1525',248)]:
    x=-10
    while x<490:
        width=r.randrange(16,37); height=r.randrange(25,83);y=base-height
        d.rectangle((x,y,x+width-3,280),fill=color)
        d.line((x,y,x+width-3,y),fill='#34425b')
        if r.random()<.25:d.line((x+width//2,y-15,x+width//2,y),fill=color)
        for xx in range(x+4,x+width-5,6):
            for yy in range(y+7,base,9):
                if r.random()<.24:d.rectangle((xx,yy,xx+1,yy+2),fill=r.choice(['#7894b6','#4b6486','#3b4e6c']))
        x+=width
# Quiet rain streaks and a rooftop in the foreground.
for _ in range(40):
    x,y=r.randrange(W),r.randrange(H);d.line((x,y,x-2,y+7),fill='#33425c')
d.rectangle((0,257,480,270),fill='#080e19');d.line((0,256,480,256),fill='#41516a')
save(im,'03-midnight-blocks.png')

im,d=canvas((10,12,18),(19,24,35))
for x in range(0,W,24):d.line((x,0,x,H),fill='#1c2636')
for y in range(6,H,24):d.line((0,y,W,y),fill='#1c2636')
# Stepped orbital arcs and small tile constellations.
for radius,color in [(84,'#334965'),(61,'#536d90'),(39,'#7f9fc4')]:
    for angle in range(12,321,2):
        a=math.radians(angle);x=354+int(math.cos(a)*radius)//2*2;y=133+int(math.sin(a)*radius)//2*2
        d.rectangle((x,y,x+1,y+1),fill=color)
for x,y,s in [(353,132,6),(415,93,4),(280,173,4),(294,66,3),(125,196,4),(78,71,3)]:
    d.rectangle((x-s,y-s,x+s,y+s),outline='#8eadd0',width=1)
    d.rectangle((x-1,y-1,x+1,y+1),fill='#8eadd0')
for x in range(31,127,8):d.rectangle((x,232,x+3,235),fill='#496582' if x<80 else '#27384e')
save(im,'04-orbital-grid.png')

im,d=canvas((12,14,22),(27,29,47));stars(d,91)
# Pixelated lunar eclipse above layered dunes.
d.ellipse((310,37,369,96),fill='#9aafd0');d.ellipse((302,28,362,87),fill='#101420')
for base,amplitude,color,phase in [(182,15,'#303951',0),(206,20,'#202b40',1),(237,14,'#141e30',2)]:
    points=[(0,270)]+[(x,int(base+math.sin(x/75+phase)*amplitude)//2*2) for x in range(0,482,2)]+[(480,270)]
    d.polygon(points,fill=color)
for x,y in [(43,222),(81,246),(192,239),(404,253)]:d.line((x,y,x+8,y),fill='#3d4e69')
save(im,'05-lunar-dunes.png')
# Preview is a contact sheet, kept outside the wallpaper chooser.
thumbs=[]
for path in sorted(OUT.glob('0[2-5]-*.png')):
    img=Image.open(path).resize((480,270),Image.Resampling.NEAREST);thumbs.append(img)
sheet=Image.new('RGB',(960,540))
for i,img in enumerate(thumbs):sheet.paste(img,((i%2)*480,(i//2)*270))
sheet.save(OUT.parent/'wallpaper-preview.png')
