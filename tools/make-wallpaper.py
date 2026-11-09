#!/usr/bin/env python3
"""Generate an original, quiet geometric wallpaper using integer pixel shapes."""
import random, struct, zlib
from pathlib import Path
w,h=1920,1080
pixels=bytearray(bytes((13,15,19))*(w*h))
def rect(x,y,ww,hh,c):
    for yy in range(max(0,y),min(h,y+hh)):
        start=(yy*w+max(0,x))*3; end=(yy*w+min(w,x+ww))*3
        if end>start: pixels[start:end]=bytes(c)*((end-start)//3)
for y in range(0,h,48): rect(0,y,w,1,(18,21,27))
for x in range(0,w,48): rect(x,0,1,h,(18,21,27))
random.seed(29)
# A stepped lunar disc and a low skyline, leaving the center calm.
for yy in range(-80,81,8):
    half=int((80**2-yy**2)**.5)//8*8
    rect(1488-half,256+yy,half*2,8,(116,145,181))
for x in range(0,w,48):
    top=random.randrange(15,21)*48
    rect(x,top,44,h-top,(22,27,36))
    rect(x,top,44,2,(44,57,76))
    for y in range(top+16,h,32):
        if random.random()<.4: rect(x+16,y,8,8,(75,100,133))
for x,y in [(1360,150),(1680,360),(1150,280),(840,180),(460,350)]:
    rect(x,y,4,12,(102,127,157));rect(x-4,y+4,12,4,(102,127,157))
def chunk(kind,data): return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
raw=b''.join(b'\0'+pixels[y*w*3:(y+1)*w*3] for y in range(h))
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b'')
p=Path.home()/'Pictures/Wallpapers/01-quiet-grid.png';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(png)
print(p)
