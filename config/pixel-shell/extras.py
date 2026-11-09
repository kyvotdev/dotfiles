#!/usr/bin/env python3
import calendar, datetime as dt, json, re, sys, os, tempfile
from pathlib import Path
from common import *
STATE=Path.home()/'.local/state/pixel-shell'
MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December']
def shift_month(year,month,delta):
    value=year*12+month-1+delta
    year,month=divmod(value,12)
    return year,month+1

def calendar_text(year,month):
    today=dt.date.today()
    lines=[f'{MONTHS[month-1]} {year}'.center(27),' Mo  Tu  We  Th  Fr  Sa  Su']
    for week in calendar.Calendar().monthdayscalendar(year,month):
        cells=[]
        for day in week:
            cells.append('    ' if not day else f'[{day:2}]' if (year,month,day)==(today.year,today.month,today.day) else f' {day:2} ')
        lines.append(''.join(cells))
    return '\n'.join(lines)

def notes(day=None):
    subprocess.Popen([str(Path.home()/'.local/bin/pixel-calendar'),'--notes'])

def calendar_menu():
    subprocess.Popen([str(Path.home()/'.local/bin/pixel-calendar')])

def plain(text):return html.unescape(re.sub('<[^>]*>','',str(text)))
def notification_center():
    while True:
        active=json.loads(run('makoctl','list','-j').stdout)
        history=json.loads(run('makoctl','history','-j').stdout)
        modes=run('makoctl','mode').stdout.splitlines()
        rows=[('Resume notifications' if 'do-not-disturb' in modes else 'Do not disturb','dnd'),('Dismiss all visible','dismiss'),('Restore last notification','restore')]
        entries=[]
        for status,items in [('VISIBLE',active),('HISTORY',history)]:
            for item in items:
                entries.append((status,item))
                rows.append((f'[{status}] {plain(item.get("app-name","App"))} · {plain(item.get("summary","Notification"))}',('item',len(entries)-1)))
        action=choose('Notifications',rows)
        if action is None:return
        if action=='dnd':run('makoctl','mode','-t','do-not-disturb')
        elif action=='dismiss':run('makoctl','dismiss','--all')
        elif action=='restore':run('makoctl','restore',check=False)
        else:
            status,item=entries[action[1]]
            options=[('Back','back'),('Copy text','copy')]
            if status=='VISIBLE':
                options.append(('Dismiss','dismiss'))
                options += [(str(title),('invoke',key)) for key,title in item.get('actions',{}).items()]
            selected=choose(plain(item.get('summary','Notification')),options,message=plain(item.get('body','')) or 'No additional text')
            if selected=='copy':subprocess.run(['wl-copy'],input=plain(item.get('summary',''))+'\n'+plain(item.get('body','')),text=True,check=True)
            elif selected=='dismiss':run('makoctl','dismiss','-n',str(item['id']))
            elif isinstance(selected,tuple):run('makoctl','invoke','-n',str(item['id']),selected[1])

def timer():
    choice=choose('Focus timer',[('10 minutes',10),('25 minutes',25),('50 minutes',50),('Custom duration','custom'),('Cancel timer','cancel')])
    if choice is None:return
    if choice=='cancel':run('systemctl','--user','stop','pixel-focus.timer',check=False);return
    if choice=='custom':
        value=menu('Minutes 1–240',[],entry=True)
        if not value:return
        if not value.isdigit() or not 1<=int(value)<=240:raise ValueError('Choose a duration between 1 and 240 minutes')
        choice=int(value)
    run('systemctl','--user','stop','pixel-focus.timer','pixel-focus.service',check=False)
    run('systemd-run','--user','--collect','--unit=pixel-focus',f'--on-active={choice}m','notify-send','-a','Pixel Shell','-u','critical','Focus timer','Time for a break.')
    notify('Focus timer',f'{choice} minutes · you can cancel from the timer menu')

if __name__=='__main__':
    commands={'calendar':calendar_menu,'notifications':notification_center,'notes':notes,'timer':timer}
    guarded(commands.get(sys.argv[1] if len(sys.argv)>1 else 'calendar',calendar_menu))
