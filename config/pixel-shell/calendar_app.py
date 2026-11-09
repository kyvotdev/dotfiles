#!/usr/bin/env python3
import datetime as dt, json, sys, logging, subprocess, re, os, signal, time
from pathlib import Path
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk, Gdk, GLib, Gio
from agenda import Agenda

class CalendarWindow(Gtk.ApplicationWindow):
    def __init__(self,app,store=None):
        super().__init__(application=app,title='Calendar · Pixel Shell')
        self.set_wmclass('pixel-calendar','pixel-calendar')
        self.set_default_size(760,510);self.set_border_width(20)
        self.store=store or Agenda();self.selected=dt.date.today();self.upcoming=False;self.editing=None;self.deleted=None
        self.connect('key-press-event',self.key)
        outer=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=16);self.add(outer)
        head=Gtk.Box(spacing=8);outer.pack_start(head,False,False,0)
        title=Gtk.Label(label='CALENDAR / AGENDA',xalign=0);title.get_style_context().add_class('heading');head.pack_start(title,True,True,0)
        self.button(head,'Today',self.today);self.button(head,'Upcoming',self.toggle_upcoming)
        columns=Gtk.Box(spacing=24);outer.pack_start(columns,True,True,0)
        left=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12);columns.pack_start(left,False,False,0)
        self.cal=Gtk.Calendar();self.cal.set_display_options(self.cal.get_display_options() | Gtk.CalendarDisplayOptions.SHOW_WEEK_NUMBERS);self.cal.connect('day-selected',self.selected_day);self.cal.connect('month-changed',lambda *_:self.mark_days());left.pack_start(self.cal,False,False,0)
        legend=Gtk.Label(label='Bold day = open notes\nUse arrows to switch months',xalign=0);legend.get_style_context().add_class('muted');left.pack_start(legend,False,False,0)
        self.jump=Gtk.Entry(placeholder_text='Jump to date · YYYY-MM-DD');self.jump.connect('activate',self.jump_to);left.pack_start(self.jump,False,False,0)
        right=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10);columns.pack_start(right,True,True,0)
        self.date_label=Gtk.Label(xalign=0);self.date_label.get_style_context().add_class('heading');right.pack_start(self.date_label,False,False,0)
        self.count_label=Gtk.Label(xalign=0);self.count_label.get_style_context().add_class('muted');right.pack_start(self.count_label,False,False,0)
        scroll=Gtk.ScrolledWindow();scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC);right.pack_start(scroll,True,True,0)
        self.listbox=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8);scroll.add(self.listbox)
        entryrow=Gtk.Box(spacing=8);right.pack_start(entryrow,False,False,0)
        self.entry=Gtk.Entry(placeholder_text='New note for selected day…');self.entry.connect('activate',self.save_note);entryrow.pack_start(self.entry,True,True,0)
        self.save=self.button(entryrow,'Add',self.save_note)
        foot=Gtk.Box(spacing=8);outer.pack_start(foot,False,False,0)
        self.status=Gtk.Label(label='Esc · close    Ctrl+N · note    Ctrl+L · date',xalign=0);self.status.get_style_context().add_class('muted');self.status.set_line_wrap(True);foot.pack_start(self.status,True,True,0)
        self.undo=self.button(foot,'Undo delete',self.undo_delete);self.undo.set_no_show_all(True);self.undo.hide()
        self.render();self.mark_days()
    def button(self,box,label,callback):
        b=Gtk.Button(label=label);b.connect('clicked',callback);box.pack_start(b,False,False,0);return b
    def safe(self,callback):
        try:return callback()
        except (ValueError,OSError) as exc:self.status.set_text(str(exc));return None
    def today(self,*_):
        date=dt.date.today();self.cal.select_month(date.month-1,date.year);self.cal.select_day(date.day);self.upcoming=False;self.render()
    def toggle_upcoming(self,*_):self.upcoming=not self.upcoming;self.render()
    def selected_day(self,*_):
        y,m,d=self.cal.get_date()
        if d:self.selected=dt.date(y,m+1,d)
        self.upcoming=False;self.editing=None
        if hasattr(self,'entry'):self.entry.set_text('');self.save.set_label('Add');self.render()
    def jump_to(self,*_):
        def go():
            date=dt.date.fromisoformat(self.jump.get_text().strip());self.cal.select_month(date.month-1,date.year);self.cal.select_day(date.day)
        self.safe(go)
    def mark_days(self):
        def mark():
            y,m,_=self.cal.get_date();self.cal.clear_marks()
            for day,items in self.store.read().items():
                date=dt.date.fromisoformat(day)
                if (date.year,date.month)==(y,m+1) and any(not n.get('done') for n in items):self.cal.mark_day(date.day)
        self.safe(mark) if hasattr(self,'status') else None
    def render(self):
        def draw():
            data=self.store.read()
            for child in self.listbox.get_children():child.destroy()
            self.date_label.set_text('UPCOMING · 30 DAYS' if self.upcoming else self.selected.strftime('%a, %d %B %Y'))
            start=dt.date.today();end=start+dt.timedelta(days=30)
            days=[day for day in sorted(data) if start<=dt.date.fromisoformat(day)<=end] if self.upcoming else [self.selected.isoformat()]
            entries=[(day,n) for day in days for n in data.get(day,[]) if not self.upcoming or not n.get('done')]
            self.count_label.set_text(f'{sum(not n.get("done") for _,n in entries)} open · {len(entries)} total')
            if not entries:
                empty=Gtk.Label(label='Nothing scheduled.\nAdd something worth remembering.',xalign=0);empty.get_style_context().add_class('muted');empty.set_margin_top(28);self.listbox.pack_start(empty,False,False,0)
            for day,note in entries:
                row=Gtk.Box(spacing=8);row.get_style_context().add_class('note-row');self.listbox.pack_start(row,False,False,0)
                check=Gtk.CheckButton();check.set_active(bool(note.get('done')));check.connect('toggled',lambda b,d=day,n=note:self.change(d,n['id'],done=b.get_active()));row.pack_start(check,False,False,0)
                text=(day+'\n' if self.upcoming else '')+note['text'];label=Gtk.Label(label=text,xalign=0);label.set_line_wrap(True);label.set_max_width_chars(32);label.set_selectable(True);row.pack_start(label,True,True,0)
                if note.get('done'):label.get_style_context().add_class('muted')
                edit=Gtk.Button();edit.set_image(Gtk.Image.new_from_file(str(Path(__file__).parent/'icons/note.svg')));edit.set_tooltip_text('Edit note');edit.connect('clicked',lambda b,d=day,n=note:self.edit_note(d,n));row.pack_start(edit,False,False,0)
                delete=Gtk.Button();delete.set_image(Gtk.Image.new_from_file(str(Path(__file__).parent/'icons/trash.svg')));delete.set_tooltip_text('Delete · undo available');delete.connect('clicked',lambda b,d=day,n=note:self.delete_note(d,n));row.pack_start(delete,False,False,0)
            self.listbox.show_all()
        self.safe(draw)
    def change(self,day,ident,**values):
        self.safe(lambda:self.store.update(day,ident,**values));GLib.idle_add(self.refresh)
    def refresh(self):self.render();self.mark_days();return False
    def edit_note(self,day,note):
        date=dt.date.fromisoformat(day);self.cal.select_month(date.month-1,date.year);self.cal.select_day(date.day)
        self.editing=(day,note['id']);self.entry.set_text(note['text']);self.save.set_label('Save');self.entry.grab_focus()
    def save_note(self,*_):
        def save():
            text=self.entry.get_text().strip()
            if not text:return
            if self.editing:self.store.update(*self.editing,text=text)
            else:self.store.add(self.selected.isoformat(),text)
            self.editing=None;self.entry.set_text('');self.save.set_label('Add');self.refresh()
        self.safe(save)
    def delete_note(self,day,note):
        def remove():self.deleted=(day,self.store.remove(day,note['id']));self.undo.show();self.refresh()
        self.safe(remove)
    def undo_delete(self,*_):
        if self.deleted:self.safe(lambda:self.store.restore(*self.deleted));self.deleted=None;self.undo.hide();self.refresh()
    def key(self,widget,event):
        if event.keyval==Gdk.KEY_Escape:self.close();return True
        if event.state&Gdk.ModifierType.CONTROL_MASK:
            if event.keyval==Gdk.KEY_n:self.entry.grab_focus();return True
            if event.keyval==Gdk.KEY_l:self.jump.grab_focus();return True
        return False

DEFAULT_PALETTE={'bg':'#0d0e10','surface':'#17191d','fg':'#d5dbe3','muted':'#8793a3','accent':'#80b7db','edge':'#363c46'}
CSS = 'window {background: %(bg)s;color:%(fg)s;} * {font-family: "Terminess Nerd Font Mono";font-size:14px;} .heading {font-weight:bold;font-size:16px;color:%(accent)s;} .muted {color:%(muted)s;} button,entry {background:%(surface)s;color:%(fg)s;border:1px solid %(edge)s;border-radius:0;padding:7px;} button:hover {border-color:%(accent)s;} calendar {background:%(surface)s;color:%(fg)s;padding:12px;font-size:16px;} calendar:selected {background:%(accent)s;color:%(bg)s;} .note-row {background:%(surface)s;padding:8px;} check {border:1px solid %(accent)s;} check:checked {background:%(accent)s;}'
def load_palette(path=None):
    path=Path(path or Path.home()/'.local/state/pixel-shell/palette.json')
    result=DEFAULT_PALETTE.copy()
    try:
        data=json.loads(path.read_text())
        if isinstance(data,dict):
            for key in result:
                value=data.get(key)
                if isinstance(value,str) and re.fullmatch(r'#[0-9a-fA-F]{6}',value):result[key]=value
    except (OSError,ValueError):pass
    return result

def check_configuration():
    for name in ('get_date','select_month','select_day','get_display_options','set_display_options','mark_day','clear_marks'):
        if not hasattr(Gtk.Calendar,name):raise RuntimeError('Unsupported GTK Calendar API: '+name)
    css=Gtk.CssProvider();css.load_from_data((CSS%load_palette()).encode())
    print('Calendar GTK3 API and CSS checks passed (display-independent)')

def restart_previous_instance():
    targets={str(Path(__file__)),str(Path(__file__).resolve()),str(Path.home()/'.config/pixel-shell/calendar_app.py')}
    stopped=[]
    for process in Path('/proc').iterdir():
        if not process.name.isdigit() or int(process.name)==os.getpid():continue
        try:
            if process.stat().st_uid!=os.getuid():continue
            args=(process/'cmdline').read_bytes().split(b'\0')
            if len(args)>1 and os.fsdecode(args[1]) in targets:
                os.kill(int(process.name),signal.SIGTERM);stopped.append(int(process.name))
        except (OSError,ValueError):pass
    deadline=time.monotonic()+2
    while stopped and time.monotonic()<deadline:
        stopped=[pid for pid in stopped if Path('/proc').joinpath(str(pid)).exists()]
        if stopped:time.sleep(.05)

def main():
    if '--check' in sys.argv:check_configuration();return
    if '--restart' in sys.argv:restart_previous_instance();sys.argv.remove('--restart')
    app=Gtk.Application(application_id='org.pixelshell.Calendar',flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
    def activate(app):
        try:
            window=app.get_active_window()
            if window is None:
                css=Gtk.CssProvider();css.load_from_data((CSS%load_palette()).encode())
                Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
                window=CalendarWindow(app);window.show_all()
            window.present()
            if getattr(app,'open_notes',False):window.entry.grab_focus()
        except Exception:
            logging.exception('Calendar startup failed')
            subprocess.run(['notify-send','-a','Pixel Shell','Calendar failed','See ~/.local/state/pixel-shell/calendar.log'],check=False)
            app.quit()
    def command_line(app,line):
        app.open_notes='--notes' in line.get_arguments();app.activate();return 0
    app.connect('activate',activate);app.connect('command-line',command_line)
    app.run(sys.argv)
if __name__=='__main__':main()
