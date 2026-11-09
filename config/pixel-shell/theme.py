#!/usr/bin/env python3
import re, colorsys, json, os, signal, subprocess, sys, tempfile, hashlib, struct, zlib, fcntl
from pathlib import Path
from common import *
HOME=Path.home(); CONFIG=HOME/'.config'; STATE=HOME/'.local/state/pixel-shell'
STATE.mkdir(parents=True,exist_ok=True)
def write(path,text):
    path=Path(path).resolve(); path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.'+path.name)
    with os.fdopen(fd,'w') as f: f.write(text)
    os.replace(tmp,path)
def rgb(h,s,v): return '#'+''.join(f'{round(c*255):02x}' for c in colorsys.hsv_to_rgb(h,s,v))
def palette(path):
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValueError('Install python-pillow to extract wallpaper colors') from exc
    with Image.open(path) as original:
        image=original.convert('RGBA')
        image.thumbnail((128,128))
        data=list(image.getdata())
    bins=[0.0]*72
    for r,g,b,alpha in data:
        h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
        if alpha<128: continue
        if .53<=h<=.68 and s>.18 and v>.12: bins[min(71,int(h*72))]+=s*v
    h=(max(range(72),key=bins.__getitem__)+.5)/72 if max(bins)>0 else .55+(hashlib.sha256(path.read_bytes()).digest()[0]/255)*.10
    return dict(bg=rgb(h,.12,.055),surface=rgb(h,.12,.095),edge=rgb(h,.15,.25),fg=rgb(h,.08,.88),muted=rgb(h,.18,.58),accent=rgb(h,.42,.86),accent2=rgb(min(.68,h+.04),.36,.80),warn='#d4bc73')
def apply(path=None):
    if path:
        path=Path(path).expanduser().resolve(strict=True)
        p=palette(path)
    else:
        path=None
        p=dict(bg='#0d0e10',surface='#17191d',edge='#363c46',fg='#d5dbe3',muted='#8793a3',accent='#80b7db',accent2='#9aafdb',warn='#d4bc73')
    bg,surface,edge,fg,muted,a,b,w=(p[k] for k in ('bg','surface','edge','fg','muted','accent','accent2','warn'))
    for icon in (CONFIG/'pixel-shell/icons').glob('*.svg'):
        write(icon,re.sub(r'stroke="#[0-9a-fA-F]{6}"',f'stroke="{a}"',icon.read_text()))
    write(CONFIG/'waybar/colors.css','\n'.join(f'@define-color {k} {v};' for k,v in p.items())+'\n')
    write(CONFIG/'niri/colors.kdl',f'''layout {{
    focus-ring {{ active-color "{a}"; inactive-color "{edge}"; urgent-color "{w}"; }}
    border {{ active-color "{a}"; inactive-color "{edge}"; urgent-color "{w}"; }}
    background-color "{bg}"
}}
overview {{ backdrop-color "{surface}"; }}
''')
    write(CONFIG/'fuzzel/fuzzel.ini',f'''[main]
font=Terminess Nerd Font Mono:style=Bold:size=12
terminal={HOME}/.local/bin/pixel-terminal -e
icon-theme=Papirus-Dark
icons-enabled=yes
width=52
lines=10
horizontal-pad=22
vertical-pad=16
inner-pad=12
line-height=28
dpi-aware=no
[colors]
background={bg[1:]}ff
text={fg[1:]}ff
prompt={a[1:]}ff
input={fg[1:]}ff
match={a[1:]}ff
selection={edge[1:]}ff
selection-text={fg[1:]}ff
selection-match={a[1:]}ff
border={a[1:]}ff
[border]
width=2
radius=0
''')
    normal=dict(black=bg,red=w,green=a,yellow=w,blue=b,magenta=b,cyan=a,white=fg)
    terminal=f'[colors.primary]\nbackground = "{bg}"\nforeground = "{fg}"\n[colors.cursor]\ntext="{bg}"\ncursor="{a}"\n[colors.selection]\ntext="{fg}"\nbackground="{edge}"\n'
    for section in ('normal','bright'):
        terminal+='[colors.'+section+']\n'+''.join(f'{k}="{v}"\n' for k,v in normal.items())
    write(CONFIG/'alacritty/colors.toml',terminal)
    kitty=f'background {bg}\nforeground {fg}\ncursor {a}\ncursor_text_color {bg}\nselection_background {edge}\nselection_foreground {fg}\n'
    for index,value in enumerate(normal.values()):
        kitty+=f'color{index} {value}\ncolor{index+8} {value}\n'
    write(CONFIG/'kitty/colors.conf',kitty)
    if shutil.which('kitty'):
        subprocess.run(['pkill','-SIGUSR1','-u',str(os.getuid()),'-x','kitty'],capture_output=True)

    write(CONFIG/'pixel-shell/colors.fish',f'''set -g fish_color_normal {fg[1:]}
set -g fish_color_command {a[1:]}
set -g fish_color_param {fg[1:]}
set -g fish_color_quote {b[1:]}
set -g fish_color_error {w[1:]}
set -g fish_color_comment {muted[1:]}
set -g fish_color_operator {b[1:]}
set -g fish_color_escape {b[1:]}
set -g fish_color_autosuggestion {muted[1:]}
set -g fish_color_search_match --background={edge[1:]}
set -g fish_pager_color_prefix {a[1:]}
set -g fish_pager_color_completion {fg[1:]}
set -g fish_pager_color_description {muted[1:]}
set -g fish_pager_color_selected_background --background={edge[1:]}
''')
    write(CONFIG/'starship.toml',f'''add_newline = false
format = "$username$hostname$directory$git_branch$git_status$cmd_duration$line_break$character"
[username]
show_always = true
style_user = "{muted}"
style_root = "{w}"
format = "[$user]($style)"
[hostname]
ssh_only = false
style = "{muted}"
format = "[@$hostname ]($style)"
[directory]
style = "{a}"
format = "[$path]($style) "
truncation_length = 3
read_only = " [RO]"
[git_branch]
symbol = "\U000f062c "
style = "{b}"
format = "[$symbol$branch]($style) "
[git_status]
style = "{w}"
format = "([$all_status$ahead_behind]($style) )"
[cmd_duration]
min_time = 2000
style = "{muted}"
format = "[$duration]($style)"
[character]
success_symbol = "[›]({a})"
error_symbol = "[›]({w})"
vimcmd_symbol = "[‹]({b})"
''')
    gtk='\n'.join(f'@define-color {key} {value};' for key,value in dict(accent_color=a,accent_bg_color=a,accent_fg_color=bg,window_bg_color=bg,window_fg_color=fg,view_bg_color=surface,view_fg_color=fg,headerbar_bg_color=surface,headerbar_fg_color=fg,card_bg_color=surface,card_fg_color=fg,popover_bg_color=surface,popover_fg_color=fg,dialog_bg_color=surface,dialog_fg_color=fg,sidebar_bg_color=surface,sidebar_fg_color=fg,warning_color=w,error_color=w,destructive_color=w,destructive_bg_color=edge,destructive_fg_color=fg,success_color=a).items())+'\n'
    for version in ('3','4'):
        write(CONFIG/f'gtk-{version}.0/gtk.css',gtk+'* { border-radius: 0; }\n')
        write(CONFIG/f'gtk-{version}.0/settings.ini','[Settings]\ngtk-theme-name=adw-gtk3-dark\ngtk-icon-theme-name=Papirus-Dark\ngtk-font-name=Terminess Nerd Font Mono 13\ngtk-cursor-theme-name=Vanilla-DMZ\ngtk-cursor-theme-size=24\ngtk-application-prefer-dark-theme=1\n')
    # QPalette roles 0..20, matching qt6ct's upstream darker.conf.
    colors=[fg,surface,edge,edge,bg,edge,fg,fg,fg,bg,bg,edge,a,bg,b,b,edge,fg,surface,fg,muted]
    for qt in ('qt5ct','qt6ct'):
        # Qt 6.6+ adds QPalette::Accent after PlaceholderText; Qt5 ends at 20.
        roles=colors+([a] if qt=='qt6ct' else [])
        scheme='[ColorScheme]\n'
        for group in ('active','inactive','disabled'):
            cs=roles.copy()
            if group=='disabled':
                for i in (0,6,8,13): cs[i]=muted
            scheme+=group+'_colors='+', '.join('#ff'+c[1:] for c in cs)+'\n'
        dest=CONFIG/qt/'colors/pixel.conf'; write(dest,scheme)
        # Rewrite the top-level config too: qtct watches this directory for changes.
        write(CONFIG/qt/(qt+'.conf'),f'[Appearance]\ncolor_scheme_path={dest}\ncustom_palette=true\nicon_theme=Papirus-Dark\nstyle=Fusion\nstandard_dialogs=default\n[Fonts]\nfixed="JetBrainsMono Nerd Font Mono,11,-1,5,63,0,0,0,0,0"\ngeneral="Terminess Nerd Font Mono,13,-1,5,50,0,0,0,0,0"\n[Interface]\nmenus_have_icons=true\ndialog_buttons_have_icons=1\n')
    write(CONFIG/'swaylock/config',f'color={bg[1:]}\nfont=Terminess Nerd Font Mono\nfont-size=20\nindicator-radius=65\nindicator-thickness=3\ninside-color={surface[1:]}\nring-color={edge[1:]}\nkey-hl-color={a[1:]}\nbs-hl-color={b[1:]}\ntext-color={fg[1:]}\nring-ver-color={a[1:]}\nring-wrong-color={w[1:]}\ntext-wrong-color={w[1:]}\ninside-wrong-color={surface[1:]}\nline-uses-inside\nshow-failed-attempts\n')
    behavior=(CONFIG/'pixel-shell/mako-behavior.conf').read_text().replace('@warning',w)
    write(CONFIG/'mako/config',f'background-color={surface}f5\ntext-color={fg}\nborder-color={edge}\nprogress-color=over {a}40\n'+behavior)
    if shutil.which('makoctl'): subprocess.run(['makoctl','reload'],capture_output=True)
    write(STATE/'palette.json',json.dumps(p,indent=2)+'\n')
    if path:
        write(STATE/'wallpaper',str(path)+'\n')
        # Terminate only the wallpaper process created by this script.
        pidfile=STATE/'swaybg.pid'
        if pidfile.exists():
            try:
                pid=int(pidfile.read_text())
                cmdline=Path(f'/proc/{pid}/cmdline').read_bytes()
                if cmdline.split(b'\0')[0].endswith(b'swaybg'): os.kill(pid,signal.SIGTERM)
            except (OSError,ValueError): pass
        if os.environ.get('WAYLAND_DISPLAY'):
            proc=subprocess.Popen(['swaybg','-i',str(path),'-m','fill'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
            write(pidfile,str(proc.pid))
    subprocess.run(['pkill','-SIGUSR2','-u',str(os.getuid()),'-x','waybar'],capture_output=True)
    if os.environ.get('DBUS_SESSION_BUS_ADDRESS'):
        for key,value in [('gtk-theme','adw-gtk3-dark'),('icon-theme','Papirus-Dark'),('cursor-theme','Vanilla-DMZ'),('color-scheme','prefer-dark'),('font-name','Terminess Nerd Font Mono 13')]:
            subprocess.run(['gsettings','set','org.gnome.desktop.interface',key,value],capture_output=True)
    print('Applied palette: '+a)

def main():
    arg=sys.argv[1] if len(sys.argv)>1 else '--restore'
    if arg=='--choose':
        folder=HOME/'Pictures/Wallpapers'; folder.mkdir(parents=True,exist_ok=True)
        files=sorted(p for p in folder.rglob('*') if p.suffix.lower() in ('.png','.jpg','.jpeg','.webp'))
        chosen=choose('Wallpaper',[(str(p.relative_to(folder)),p) for p in files])
        if chosen: apply(chosen)
    elif arg=='--restore':
        old=STATE/'wallpaper'; apply(old.read_text().strip() if old.exists() else None)
    elif arg=='--default': apply()
    else: apply(arg)
if __name__=='__main__':
    with open(STATE/'theme.lock','w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        guarded(main)
