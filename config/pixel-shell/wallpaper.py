#!/usr/bin/env python3
import random, sys
from pathlib import Path
from common import *
FOLDER=Path.home()/'Pictures/Wallpapers'
STATE=Path.home()/'.local/state/pixel-shell/wallpaper'
def files():
    FOLDER.mkdir(parents=True,exist_ok=True)
    return sorted({p.resolve() for p in FOLDER.rglob('*') if p.is_file() and p.suffix.lower() in ('.png','.jpg','.jpeg','.webp')})
def next_wallpaper(images,current):
    if not images:return None
    return images[(images.index(current)+1)%len(images)] if current in images else images[0]
def main():
    images=files()
    current=Path(STATE.read_text().strip()).resolve() if STATE.exists() else None
    action=sys.argv[1] if len(sys.argv)>1 else choose('Wallpaper',[(IC['image']+'  Choose image','choose'),(IC['shuffle']+'  Random wallpaper','random'),(IC['next']+'  Next wallpaper','next'),(IC['refresh']+'  Reapply current theme','restore'),(IC['folder']+'  Open wallpaper folder','folder')],message='Current: '+(current.name if current else 'None'))
    if not action:return
    if action=='folder':subprocess.Popen(['xdg-open',str(FOLDER)]);return
    if action=='restore':run(str(Path.home()/'.local/bin/pixel-theme'),'--restore');return
    if not images:return notify('Wallpapers','Add PNG, JPEG or WebP images to ~/Pictures/Wallpapers')
    if action=='choose':target=choose('Choose wallpaper',[(p.name+('  [current]' if p==current else ''),p) for p in images])
    elif action=='random':target=random.choice([p for p in images if p!=current] or images)
    elif action=='next':target=next_wallpaper(images,current)
    else:raise ValueError('Use choose, random, next, restore or folder')
    if target:run(str(Path.home()/'.local/bin/pixel-theme'),str(target));notify('Wallpaper applied',html.escape(target.name))
if __name__=='__main__':guarded(main)
