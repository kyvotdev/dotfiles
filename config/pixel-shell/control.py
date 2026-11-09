#!/usr/bin/env python3
import sys, os, json, secrets, subprocess, uuid
from pathlib import Path
from common import *

def fields(line):
    result, part, escaped=[], '', False
    for c in line:
        if escaped: part+=c; escaped=False
        elif c=='\\': escaped=True
        elif c==':': result.append(part); part=''
        else: part+=c
    return result+[part]

def wifi():
    devices=[fields(x) for x in run('nmcli','-t','-f','DEVICE,TYPE,STATE','device').stdout.splitlines()]
    devices=[x for x in devices if x[1]=='wifi']
    if not devices: return notify('Wi-Fi','No wireless adapter found')
    dev=choose('Wi-Fi adapter',[(f'{d}  [{s}]',d) for d,t,s in devices]) if len(devices)>1 else devices[0][0]
    if not dev: return
    while True:
        data=run('nmcli','-t','--escape','yes','-f','IN-USE,SSID,SIGNAL,SECURITY','device','wifi','list','ifname',dev,'--rescan','auto').stdout
        rows=[(IC['power']+'  Toggle Wi-Fi','toggle'),(IC['refresh']+'  Scan again','scan'),('Disconnect','disconnect'),('Hidden network','hidden'),('Saved connections','saved'),('Hotspot','hotspot')]
        seen=set()
        for line in data.splitlines():
            active,ssid,signal,security=fields(line)
            if not ssid or ssid in seen: continue
            seen.add(ssid)
            rows.append((f'{IC["wifi"]}  {ssid[:26]:<26}  {signal:>3}%  {security or "Open"}'+('  [connected]' if active else ''),('connect',ssid)))
        action=choose('Network',rows)
        if action is None: return
        if action=='scan': run('nmcli','device','wifi','rescan','ifname',dev); continue
        if action=='toggle':
            on=run('nmcli','radio','wifi').stdout.strip()=='enabled'
            run('nmcli','radio','wifi','off' if on else 'on'); return
        if action=='disconnect': run('nmcli','device','disconnect',dev); return
        if action=='hotspot': hotspot(); return
        if action=='saved':
            profiles=[fields(l) for l in run('nmcli','-t','-f','NAME,UUID,TYPE','connection','show').stdout.splitlines()]
            profile=choose('Saved Wi-Fi',[(n,u) for n,u,t in profiles if t=='802-11-wireless'])
            if not profile: continue
            op=choose('Connection',[('Connect','up'),('Forget','delete')])
            if op=='up': terminal('nmcli','--ask','connection','up','uuid',profile)
            if op=='delete' and confirm('Forget this connection?'): run('nmcli','connection','delete','uuid',profile)
            return
        if action=='hidden':
            ssid=menu('Network SSID',[],entry=True)
            if ssid: terminal('nmcli','--ask','device','wifi','connect',ssid,'ifname',dev,'hidden','yes')
            return
        if isinstance(action,tuple):
            # NetworkManager handles stored secrets, PSK, 802.1X and its own prompts.
            terminal('nmcli','--ask','device','wifi','connect',action[1],'ifname',dev)
            return

def hotspot():
    import dbus
    bus=dbus.SystemBus()
    manager=dbus.Interface(bus.get_object('org.freedesktop.NetworkManager','/org/freedesktop/NetworkManager/Settings'),'org.freedesktop.NetworkManager.Settings')
    profiles=[]
    for path in manager.ListConnections():
        conn=dbus.Interface(bus.get_object('org.freedesktop.NetworkManager',path),'org.freedesktop.NetworkManager.Settings.Connection')
        data=conn.GetSettings()
        if data.get('connection',{}).get('id')=='Pixel-Link': profiles.append((conn,data))
    action=choose('Hotspot',[('Start Pixel-Link','start'),('Stop Pixel-Link','stop'),('Show password','show'),('Delete hotspot profile','delete')])
    if not action: return
    if action=='stop': run('nmcli','connection','down','id','Pixel-Link'); return
    if action=='delete':
        if confirm('Delete hotspot?'):
            for conn,data in profiles: conn.Delete()
        return
    if action=='show':
        if not profiles: return notify('Hotspot','Create the hotspot first')
        key=profiles[0][0].GetSecrets('802-11-wireless-security')['802-11-wireless-security'].get('psk','Unavailable')
        menu('Hotspot password',[str(key)],entry=False); return
    devices=[fields(x) for x in run('nmcli','-t','-f','DEVICE,TYPE','device').stdout.splitlines()]
    devices=[d for d,t in devices if t=='wifi']
    dev=choose('Hotspot adapter',[(d,d) for d in devices])
    if not dev: return
    if not confirm('Start hotspot? Wi-Fi on this adapter will disconnect'): return
    if not profiles:
        uid=str(uuid.uuid4())
        settings={
          'connection': {'id':'Pixel-Link','uuid':uid,'type':'802-11-wireless','autoconnect':False,'interface-name':dev},
          '802-11-wireless': {'ssid':dbus.ByteArray(b'Pixel-Link'),'mode':'ap','band':'bg'},
          '802-11-wireless-security': {'key-mgmt':'wpa-psk','psk':secrets.token_urlsafe(15)},
          'ipv4':{'method':'shared'}, 'ipv6':{'method':'disabled'}}
        manager.AddConnection(dbus.Dictionary({k:dbus.Dictionary(v,signature='sv') for k,v in settings.items()},signature='sa{sv}'))
    run('nmcli','connection','up','id','Pixel-Link','ifname',dev)
    notify('Hotspot active','Pixel-Link · use Show password to view credentials')

def power():
    action=choose('Session',[(IC['lock']+'  Lock','lock'),(IC['moon']+'  Suspend','suspend'),('Log out','logout'),(IC['refresh']+'  Reboot','reboot'),(IC['power']+'  Shut down','poweroff')])
    if not action: return
    if action=='lock': run('swaylock','-f'); return
    if action=='suspend':
        run('swaylock','-f'); run('systemctl','suspend'); return
    if not confirm(action.capitalize()+'?'): return
    if action=='logout': run('niri','msg','action','quit','--skip-confirmation')
    else: run('systemctl',action)

def audio():
    action=choose('Audio',[('Select output','sinks'),('Select microphone','sources'),('Toggle output mute','mute'),('Toggle microphone mute','mic')])
    if action in ('mute','mic'):
        run('wpctl','set-mute','@DEFAULT_AUDIO_SOURCE@' if action=='mic' else '@DEFAULT_AUDIO_SINK@','toggle'); return
    if action not in ('sinks','sources'): return
    # pw-dump exposes numeric object IDs without parsing localized wpctl trees.
    nodes=json.loads(run('pw-dump').stdout)
    cls='Audio/Sink' if action=='sinks' else 'Audio/Source'
    rows=[]
    for node in nodes:
        props=node.get('info',{}).get('props',{})
        if props.get('media.class')==cls:
            rows.append((props.get('node.description',props.get('node.name','Device')),str(node['id'])))
    target=choose('Default device',rows)
    if target: run('wpctl','set-default',target)

def tools_menu():
    choice=choose('Control center',[('Displays','displays'),('Calendar','calendar'),('Notifications','notifications'),('Notes','notes'),('Focus timer','timer'),(IC['wifi']+'  Network','wifi'),(IC['bt']+'  Bluetooth','bluetooth'),(IC['wifi']+'  Hotspot','hotspot'),(IC['sound']+'  Audio devices','audio'),(IC['image']+'  Wallpaper','wallpaper'),(IC['moon']+'  Caffeine','idle'),(IC['power']+'  Session','power')])
    if choice in ('calendar','notifications','notes','timer'):
        subprocess.Popen([str(Path.home()/'.local/bin/pixel-extras'),choice])
    elif choice=='bluetooth': subprocess.Popen([str(Path.home()/'.local/bin/pixel-bluetooth')])
    elif choice=='wallpaper': subprocess.Popen([str(Path.home()/'.local/bin/pixel-wallpaper')])
    elif choice=='idle':
        run(str(Path.home()/'.local/bin/pixel-caffeine'),'toggle')
    elif choice=='displays':
        subprocess.Popen([str(Path.home()/'.local/bin/pixel-displays')])
    elif choice: globals()[choice]()

if __name__=='__main__':
    commands={'wifi':wifi,'hotspot':hotspot,'power':power,'audio':audio,'menu':tools_menu}
    guarded(commands.get(sys.argv[1] if len(sys.argv)>1 else 'menu',tools_menu))
