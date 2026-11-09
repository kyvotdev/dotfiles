#!/usr/bin/env python3
"""niri display control with an independent rollback watchdog."""
import json, os, sys, time, uuid, tempfile, signal, fcntl
from pathlib import Path
from common import *
STATE=Path.home()/'.local/state/pixel-shell'
SCRIPT=Path(__file__).resolve()
def outputs():return json.loads(run('niri','msg','-j','outputs').stdout)
def command(name,*args,check=True):return run('niri','msg','output',name,*map(str,args),check=check,timeout=5)
def active(out):return out.get('current_mode') is not None and bool(out.get('logical'))
def mode_name(mode):return f'{mode["width"]}x{mode["height"]}@{mode["refresh_rate"]/1000:.3f}'
def transform_name(value):
    return {'Normal':'normal','Flipped':'flipped','Flipped90':'flipped-90','Flipped180':'flipped-180','Flipped270':'flipped-270'}.get(value,value)
def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.display-')
    with os.fdopen(fd,'w') as f:json.dump(data,f)
    os.replace(tmp,path)
def restore(snapshot):
    current=outputs();usable=[n for n,o in snapshot.items() if n in current and active(o)]
    if not usable:
        for n in current:command(n,'on',check=False)
        return
    for n in usable:command(n,'on',check=False)
    for n in usable:
        o=snapshot[n];logic=o['logical'];mode=o['modes'][o['current_mode']]
        command(n,'mode',mode_name(mode),check=False)
        command(n,'scale',logic['scale'],check=False)
        command(n,'transform',transform_name(logic.get('transform','normal')),check=False)
        command(n,'position','set',logic['x'],logic['y'],check=False)
    for n,o in snapshot.items():
        if n in current and not active(o):command(n,'off',check=False)
def guarded_change(change):
    STATE.mkdir(parents=True,exist_ok=True)
    with open(STATE/'display-change.lock','a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('Another display change is waiting for confirmation')
        snapshot=outputs()
        if not any(active(o) for o in snapshot.values()):raise ValueError('No active display to restore')
        path=STATE/'display-transactions'/(str(uuid.uuid4())+'.json')
        record={'status':'pending','deadline':time.time()+40,'outputs':snapshot};atomic(path,record)
        with open(STATE/'display-watchdog.log','a') as log:
            proc=subprocess.Popen([sys.executable,str(SCRIPT),'--watchdog',str(path)],stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
        kept=False
        try:
            change(snapshot)
            kept=choose('Keep display settings?', [('Keep this layout',True),('Revert now',False)],message='Automatic rollback in 15 seconds. Esc also reverts.',timeout=15) is True
        finally:
            if not kept:restore(snapshot)
            record['status']='kept' if kept else 'reverted';atomic(path,record)
            try:proc.wait(timeout=2)
            except subprocess.TimeoutExpired:pass
            if record['status']!='pending':path.unlink(missing_ok=True)
        if kept:notify('Displays','Layout applied · use Save layout to keep it across logins')
def watchdog(path):
    path=Path(path)
    while path.exists():
        record=json.loads(path.read_text())
        if record['status']!='pending':return
        if time.time()>=record['deadline']:
            restore(record['outputs']);record['status']='reverted';atomic(path,record);return
        time.sleep(.25)
def wait_active(name):
    for _ in range(30):
        current=outputs()
        if name not in current:raise ValueError('Display disconnected: '+name)
        if active(current[name]):return current[name]
        time.sleep(.1)
    raise ValueError('Display did not become active: '+name)
def select_output(title,data,exclude=None):
    rows=[]
    for name,out in data.items():
        if name==exclude:continue
        status=mode_name(out['modes'][out['current_mode']]) if active(out) else 'off'
        rows.append((f'{name} · {out.get("model","")} · {status}',name))
    return choose(title,rows)
def only(name):
    def apply(snapshot):
        command(name,'on');wait_active(name)
        for other in snapshot:
            if other!=name:command(other,'off')
        command(name,'position','set',0,0)
        run('niri','msg','action','focus-monitor',name)
    guarded_change(apply)
def extend(base,target,direction):
    def apply(snapshot):
        command(base,'on');command(target,'on')
        a=wait_active(base)['logical'];b=wait_active(target)['logical']
        positions={'right':(a['x']+a['width'],a['y']), 'left':(a['x']-b['width'],a['y']), 'above':(a['x'],a['y']-b['height']), 'below':(a['x'],a['y']+a['height'])}
        command(target,'position','set',*positions[direction])
    guarded_change(apply)
def stop_mirror():run('systemctl','--user','stop','pixel-mirror.service',check=False)
def mirror(source,target):
    if not shutil.which('wl-mirror'):raise ValueError('Install mirroring support: sudo pacman -S --needed wl-mirror')
    if source==target:raise ValueError('Choose two different displays')
    def apply(snapshot):command(source,'on');command(target,'on');wait_active(source);wait_active(target)
    guarded_change(apply)
    stop_mirror()
    cmd=['systemd-run','--user','--collect','--unit=pixel-mirror']
    for key in ('WAYLAND_DISPLAY','DISPLAY','XDG_RUNTIME_DIR'):
        if key in os.environ:cmd.append('--setenv='+key+'='+os.environ[key])
    cmd+=['wl-mirror','--backend','extcopy','--fullscreen-output',target,'--title','Pixel Mirror',source]
    run(*cmd)
    time.sleep(.7)
    if run('systemctl','--user','is-active','pixel-mirror.service',check=False).returncode:
        raise ValueError('Mirror could not start. See: journalctl --user -u pixel-mirror.service -b')
    notify('Screen mirroring',source+' → '+target+' · stop from the display menu')
def settings(data):
    target=select_output('Display settings',data)
    if not target:return
    choice=choose(target,[('Resolution / refresh rate','mode'),('Scale','scale'),('Rotation','rotate'),('Enable','on'),('Disable','off')])
    if not choice:return
    if choice=='mode':
        value=choose('Resolution',[(mode_name(m)+(' · recommended' if m.get('is_preferred') else ''),mode_name(m)) for m in data[target]['modes']])
        if value:guarded_change(lambda _:command(target,'mode',value))
    elif choice=='scale':
        value=choose('Scale',[(f'{int(v*100)}%',str(v)) for v in (1,1.25,1.5,1.75,2)])
        if value:guarded_change(lambda _:command(target,'scale',value))
    elif choice=='rotate':
        value=choose('Rotation',[(x,x) for x in ('normal','90','180','270')])
        if value:guarded_change(lambda _:command(target,'transform',value))
    else:
        if choice=='off' and sum(active(o) for o in data.values())<=1 and active(data[target]):raise ValueError('The last active display cannot be disabled')
        guarded_change(lambda _:command(target,choice))
def save_layout():
    data=outputs();lines=['// Saved with pixel-displays.']
    for name,out in data.items():
        lines.append('output '+json.dumps(name)+' {')
        if active(out):
            logic=out['logical'];lines += ['    mode '+json.dumps(mode_name(out['modes'][out['current_mode']])),'    scale '+str(logic['scale']),'    transform '+json.dumps(transform_name(logic.get('transform','normal'))),f'    position x={logic["x"]} y={logic["y"]}']
        else:lines.append('    off')
        lines.append('}')
    path=Path.home()/'.config/niri/monitors.kdl';target=path.resolve();old=target.read_text() if target.exists() else ''
    target.write_text('\n'.join(lines)+'\n')
    if run('niri','validate',check=False).returncode:target.write_text(old);raise ValueError('Saved layout rejected; previous file restored')
    atomic(STATE/'display-layout.json',data);notify('Displays','Layout saved for the next session')
def main():
    action=sys.argv[1] if len(sys.argv)>1 else 'menu'
    if action=='rescue':
        for n in outputs():command(n,'on',check=False);command(n,'mode','auto',check=False);command(n,'position','auto',check=False)
        stop_mirror();return
    if action=='stop-mirror':stop_mirror();return
    if action=='status':print(json.dumps(outputs(),indent=2));return
    while True:
        data=outputs()
        action=choose('Displays', [('Internal display only','internal'),('External / HDMI only','external'),('Extend desktop','extend'),('Mirror to another display','mirror'),('Stop mirroring','stop'),('Per-display settings','settings'),('Save current layout','save'),('Restore saved layout','restore'),('Enable all · automatic layout','all')],message='\n'.join(n+' · '+('active' if active(o) else 'off') for n,o in data.items()))
        if not action:return
        if action=='stop':stop_mirror()
        elif action=='save':save_layout()
        elif action=='settings':settings(data)
        elif action in ('internal','external'):
            choices={n:o for n,o in data.items() if (n.startswith(('eDP','LVDS','DSI')))==(action=='internal')}
            target=select_output('Use this display',choices)
            if target:stop_mirror();only(target)
        elif action in ('extend','mirror'):
            base=select_output('Source / main display',data)
            if not base:continue
            target=select_output('Target display',data,exclude=base)
            if not target:continue
            if action=='mirror':mirror(base,target)
            else:
                direction=choose('Place target display',[(x.title(),x) for x in ('right','left','above','below')])
                if direction:stop_mirror();extend(base,target,direction)
        elif action=='restore':
            path=STATE/'display-layout.json'
            if not path.exists():raise ValueError('No saved display layout')
            guarded_change(lambda _:restore(json.loads(path.read_text())))
        elif action=='all':
            def enable(snapshot):
                for n in snapshot:command(n,'on');command(n,'position','auto')
            guarded_change(enable)
def watch_outputs():
    while True:
        try:
            data=outputs()
            if data and not any(active(o) for o in data.values()):
                builtins=[name for name in data if name.startswith(('eDP','LVDS','DSI'))]
                for name in builtins or list(data):command(name,'on',check=False)
        except (OSError,ValueError,subprocess.SubprocessError):pass
        time.sleep(3)

if __name__=='__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--watchdog':watchdog(sys.argv[2])
    elif len(sys.argv)>1 and sys.argv[1]=='--watch-outputs':watch_outputs()
    else:guarded(main)
