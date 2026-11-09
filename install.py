#!/usr/bin/env python3
"""Link this dotfiles tree, preserving conflicting files before replacing them."""
from pathlib import Path
from datetime import datetime
import shutil
root=Path(__file__).resolve().parent
home=Path.home()
backup=root/'backups'/datetime.now().strftime('%Y%m%d-%H%M%S')
# Adapt the prepared configuration when cloning under another home directory.
if str(home)!='/home/didi':
    for path in (root/'config').rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts: continue
        try: text=path.read_text()
        except UnicodeDecodeError: continue
        if '/home/didi' in text:path.write_text(text.replace('/home/didi',str(home)))
for filename,text in [('active-gpu.kdl','// Automatic GPU selection.\n'),('monitors.kdl','// Save a local monitor layout with pixel-displays.\n')]:
    path=root/'config/niri'/filename
    if not path.exists():path.write_text(text)
def link(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.is_symlink() and target.resolve()==source.resolve(): return
    if target.exists() or target.is_symlink():
        dest=backup/target.relative_to(home); dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.move(str(target),str(dest)); print('Backup:',dest)
    target.symlink_to(source, target_is_directory=source.is_dir())
    print('Linked:',target)
for source in (root/'config').iterdir():
    if source.name=='systemd':
        for unit in (source/'user').glob('*.service'): link(unit,home/'.config/systemd/user'/unit.name)
    else: link(source,home/'.config'/source.name)
for source in (root/'bin').iterdir():
    if source.is_file() and source.name.startswith('pixel-'): link(source,home/'.local/bin'/source.name)
for source in (root/'assets/wallpapers').iterdir(): link(source,home/'Pictures/Wallpapers'/source.name)
print('Links ready. Run ~/.local/bin/pixel-doctor before activation.')
