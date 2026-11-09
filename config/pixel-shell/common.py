import os, subprocess, shutil, html
import dbus
from pathlib import Path
ROOT = Path.home()/'.config/pixel-shell'
IC = dict(wifi='\U000f05a9', bt='\U000f00af', power='\U000f0425', lock='\U000f033e', screen='\U000f0379', sound='\U000f057e', moon='\U000f0594', refresh='\U000f0450', settings='\U000f0493', image='\U000f02e9', check='\U000f012c')
IC.update(calendar='\U000f00ed', bell='\U000f009a', note='\U000f082e', timer='\U000f0150', folder='\U000f024b', shuffle='\U000f049d', next='\U000f04ad', cancel='\U000f0156', copy='\U000f018f', trash='\U000f01b4')
def run(*args, check=True, timeout=35):
    return subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=check, env={**os.environ,'LC_ALL':'C'})
def notify(title, body=''):
    subprocess.run(['notify-send','-a','Pixel Shell','-i','preferences-system',title,body], check=False)
def menu(title, rows, password=False, entry=False, message=None, icons=None, timeout=None):
    cmd=['fuzzel','--dmenu','--prompt',title.upper()+' / ', '--width','52']
    if message: cmd += ['--mesg',message]
    if password: cmd += ['--password','*']
    if not entry: cmd += ['--index']
    lines=[]
    for i,row in enumerate(rows):
        label=''.join(c if c.isprintable() else ' ' for c in row)
        if icons and i<len(icons): label+='\0icon\x1f'+str(icons[i])
        lines.append(label)
    try: p=subprocess.run(cmd,input='\n'.join(lines),text=True,capture_output=True,timeout=timeout)
    except subprocess.TimeoutExpired: return None
    if p.returncode: return None
    value=p.stdout.rstrip('\n')
    if entry: return value
    try: return int(value)
    except ValueError: return None

def choose(title, rows, message=None, timeout=None):
    default='settings'
    for word,key in (('bluetooth','bt'),('network','wifi'),('wi-fi','wifi'),('hotspot','wifi'),('display','screen'),('hdmi','screen'),('caffeine','moon'),('audio','sound'),('session','power'),('wallpaper','image'),('calendar','calendar'),('notification','bell'),('note','note'),('timer','timer')):
        if word in title.lower(): default=key;break
    labels=[];icons=[]
    reverse={v:k for k,v in IC.items()}
    for label,value in rows:
        key=default
        if label and 0xF0000<=ord(label[0])<=0x10FFFF:
            key=reverse.get(label[0],default);label=label[1:].lstrip()
        for word,action_icon in (('cancel','cancel'),('delete','trash'),('forget','trash'),('copy','copy'),('refresh','refresh'),('scan','refresh'),('unlock','lock'),('lock','lock'),('reboot','refresh'),('shut down','power'),('power','power'),('suspend','moon'),('calendar','calendar'),('notification','bell'),('notes','note'),('timer','timer'),('bluetooth','bt'),('network','wifi'),('hotspot','wifi'),('wallpaper','image'),('audio','sound'),('disconnect','unlink'),('connect','link'),('pair','link'),('trust','check'),('block','cancel'),('previous','prev'),('next','next'),('today','calendar'),('add note','note'),('show password','lock')):
            if word in label.lower(): key=action_icon;break
        labels.append(label)
        icons.append(ROOT/'icons'/(key+'.svg'))
    i=menu(title,labels,message=message,icons=icons,timeout=timeout)
    return rows[i][1] if i is not None and 0 <= i < len(rows) else None

def confirm(title): return choose(title,[('Cancel',False),(IC['check']+'  Confirm',True)]) is True

def terminal(*args):
    cmd=['kitty','--hold',*args] if shutil.which('kitty') else ['alacritty','--hold','-e',*args]
    return subprocess.Popen(cmd,env={**os.environ,'LC_ALL':'C','NO_COLOR':'1'})

def guarded(fn):
    try: fn()
    except (subprocess.SubprocessError, OSError, ValueError, dbus.DBusException) as e:
        notify('Action failed',html.escape(getattr(e,'stderr','') or str(e)))
        raise SystemExit(1)
