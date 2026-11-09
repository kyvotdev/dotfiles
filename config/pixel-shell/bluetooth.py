#!/usr/bin/env python3
import sys, subprocess, signal, html
import dbus, dbus.service, dbus.mainloop.glib
from gi.repository import GLib
from common import *
BLUEZ='org.bluez'
AGENT='org.bluez.Agent1'
PATH='/org/pixelshell/Agent'
class Rejected(dbus.DBusException): _dbus_error_name='org.bluez.Error.Rejected'

def props(bus,path,iface):
    return dbus.Interface(bus.get_object(BLUEZ,path),'org.freedesktop.DBus.Properties').GetAll(iface)
def objects(bus):
    return dbus.Interface(bus.get_object(BLUEZ,'/'),'org.freedesktop.DBus.ObjectManager').GetManagedObjects()

class Agent(dbus.service.Object):
    def __init__(self,bus):
        super().__init__(bus,PATH)
        self.bus=bus; self.pending=None; self.loop=None
    def name(self,device):
        try: return str(props(self.bus,device,'org.bluez.Device1').get('Alias',device))
        except dbus.DBusException: return str(device)
    def ask(self,device,prompt,secret=False,confirm_only=False):
        if self.pending: raise Rejected('Another pairing request is open')
        cmd=['fuzzel','--dmenu','--prompt',IC['bt']+'  BLUETOOTH / ','--mesg',self.name(device)+'\n'+prompt]
        if secret: cmd+=['--password','*']
        if confirm_only: cmd+=['--index']
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
        proc.stdin.write('Reject\0icon\x1f'+str(ROOT/'icons/cancel.svg')+'\nAccept\0icon\x1f'+str(ROOT/'icons/check.svg')+'\n' if confirm_only else '')
        proc.stdin.close()
        self.pending=proc; self.loop=GLib.MainLoop()
        def poll():
            if proc.poll() is None: return True
            self.loop.quit(); return False
        GLib.timeout_add(75,poll)
        self.loop.run()
        response=proc.stdout.read().strip(); self.pending=None
        if proc.returncode or (confirm_only and response!='1'): raise Rejected('Rejected by user')
        return response
    @dbus.service.method(AGENT,in_signature='',out_signature='')
    def Release(self): self.Cancel(); GLib.idle_add(lambda: sys.exit(0))
    @dbus.service.method(AGENT,in_signature='o',out_signature='s')
    def RequestPinCode(self,device):
        pin=self.ask(device,'Enter the device PIN',secret=True)
        if not 1<=len(pin)<=16: raise Rejected('Invalid PIN')
        return pin
    @dbus.service.method(AGENT,in_signature='o',out_signature='u')
    def RequestPasskey(self,device):
        pin=self.ask(device,'Enter six-digit passkey',secret=True)
        if not pin.isascii() or not pin.isdigit() or not 1<=len(pin)<=6: raise Rejected('Invalid passkey')
        return dbus.UInt32(int(pin))
    @dbus.service.method(AGENT,in_signature='os',out_signature='')
    def DisplayPinCode(self,device,pincode): notify('Bluetooth PIN',html.escape(self.name(device))+': '+str(pincode))
    @dbus.service.method(AGENT,in_signature='ouq',out_signature='')
    def DisplayPasskey(self,device,passkey,entered): notify('Bluetooth passkey',html.escape(self.name(device))+f': {int(passkey):06d} · {entered}/6 entered')
    @dbus.service.method(AGENT,in_signature='ou',out_signature='')
    def RequestConfirmation(self,device,passkey): self.ask(device,f'Does the device show {int(passkey):06d}?',confirm_only=True)
    @dbus.service.method(AGENT,in_signature='o',out_signature='')
    def RequestAuthorization(self,device): self.ask(device,'Allow incoming pairing?',confirm_only=True)
    @dbus.service.method(AGENT,in_signature='os',out_signature='')
    def AuthorizeService(self,device,uuid): self.ask(device,'Allow service connection?\n'+str(uuid),confirm_only=True)
    @dbus.service.method(AGENT,in_signature='',out_signature='')
    def Cancel(self):
        if self.pending and self.pending.poll() is None: self.pending.terminate()

def daemon():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus=dbus.SystemBus()
    agent=Agent(bus)
    manager=dbus.Interface(bus.get_object(BLUEZ,'/org/bluez'),'org.bluez.AgentManager1')
    manager.RegisterAgent(PATH,'KeyboardDisplay'); manager.RequestDefaultAgent(PATH)
    GLib.MainLoop().run()

def bluetooth():
    bus=dbus.SystemBus()
    if run('systemctl','--user','is-active','pixel-bluetooth.service',check=False).returncode:
        run('systemctl','--user','start','pixel-bluetooth.service')
    adapters=[(p,i['org.bluez.Adapter1']) for p,i in objects(bus).items() if 'org.bluez.Adapter1' in i]
    path=choose('Bluetooth adapter',[(str(i.get('Alias',p)),p) for p,i in adapters]) if len(adapters)>1 else (adapters[0][0] if adapters else None)
    if not path: return notify('Bluetooth','No Bluetooth adapter found')
    adapter=dbus.Interface(bus.get_object(BLUEZ,path),'org.bluez.Adapter1')
    settings=dbus.Interface(bus.get_object(BLUEZ,path),'org.freedesktop.DBus.Properties')
    scanning=False
    try:
        while True:
            state=props(bus,path,'org.bluez.Adapter1')
            rows=[(IC['power']+'  Power '+('off' if state['Powered'] else 'on'),'power'),(IC['refresh']+'  Scan / refresh','scan'),('Allow incoming pairing for 120 seconds','incoming'),('Stop accepting incoming pairing','private')]
            for p,i in objects(bus).items():
                d=i.get('org.bluez.Device1')
                if d and str(d.get('Adapter'))==str(path):
                    status='connected' if d.get('Connected') else 'paired' if d.get('Paired') else 'available'
                    rows.append((IC['bt']+'  '+str(d.get('Alias',d.get('Address')))+'  ['+status+']',p))
            action=choose('Bluetooth',rows)
            if not action: return
            if action=='power': settings.Set('org.bluez.Adapter1','Powered',dbus.Boolean(not state['Powered'])); continue
            if action=='incoming':
                settings.Set('org.bluez.Adapter1','Powered',dbus.Boolean(True))
                for key,value in [('DiscoverableTimeout',dbus.UInt32(120)),('PairableTimeout',dbus.UInt32(120)),('Pairable',dbus.Boolean(True)),('Discoverable',dbus.Boolean(True))]: settings.Set('org.bluez.Adapter1',key,value)
                notify('Bluetooth','Incoming pairing enabled for 120 seconds'); continue
            if action=='private':
                settings.Set('org.bluez.Adapter1','Discoverable',dbus.Boolean(False)); settings.Set('org.bluez.Adapter1','Pairable',dbus.Boolean(False)); continue
            if action=='scan':
                settings.Set('org.bluez.Adapter1','Powered',dbus.Boolean(True))
                if not scanning: adapter.StartDiscovery(); scanning=True
                notify('Bluetooth','Scanning · open a device or choose Scan / refresh again'); continue
            device=dbus.Interface(bus.get_object(BLUEZ,action),'org.bluez.Device1')
            d=props(bus,action,'org.bluez.Device1')
            op=choose(str(d.get('Alias','Device')),[('Pair','pair'),('Connect','connect'),('Disconnect','disconnect'),('Untrust' if d.get('Trusted') else 'Trust','trust'),('Unblock' if d.get('Blocked') else 'Block','block'),('Forget device','forget')])
            if op=='pair':
                notify('Bluetooth','Pairing · follow the confirmation prompt')
                device.Pair(timeout=120)
                notify('Bluetooth','Paired · choose Connect to use this device')
            elif op=='connect': device.Connect(timeout=60)
            elif op=='disconnect': device.Disconnect()
            elif op in ('trust','block'):
                key='Trusted' if op=='trust' else 'Blocked'
                dbus.Interface(bus.get_object(BLUEZ,action),'org.freedesktop.DBus.Properties').Set('org.bluez.Device1',key,dbus.Boolean(not d.get(key)))
            elif op=='forget' and confirm('Forget this device?'): adapter.RemoveDevice(action)
    finally:
        if scanning:
            try: adapter.StopDiscovery()
            except dbus.DBusException: pass

if __name__=='__main__':
    try: daemon() if '--agent' in sys.argv else guarded(bluetooth)
    except dbus.DBusException as e:
        notify('Bluetooth error',html.escape(str(e))); sys.exit(1)
