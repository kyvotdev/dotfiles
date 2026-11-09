#!/usr/bin/env python3
"""Install missing editor plugins without blocking the Neovim UI."""
import argparse,fcntl,json,os,shutil,subprocess,sys,uuid,tempfile
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--update',action='store_true',help='update already installed plugins with git pull --ff-only')
options=parser.parse_args()
home=Path.home();app=os.getenv('NVIM_APPNAME','nvim')
data=Path(os.getenv('XDG_DATA_HOME',str(home/'.local/share')))/app
state=Path(os.getenv('XDG_STATE_HOME',str(home/'.local/state')))/app
state.mkdir(parents=True,exist_ok=True)
specs=json.loads((Path(__file__).resolve().parents[1]/'plugins.json').read_text())
def install():
    errors=[];revisions={}
    for spec in specs:
        target=data/'site/pack/pixel/start'/spec['name'];target.parent.mkdir(parents=True,exist_ok=True)
        stage=target.with_name(target.name+'.download-'+uuid.uuid4().hex)
        try:
            if not target.exists():
                result=subprocess.run(['git','clone','--filter=blob:none','--branch',spec['branch'],spec['url'],str(stage)],text=True,capture_output=True,timeout=90)
                if result.returncode:raise RuntimeError(result.stderr.strip())
                stage.rename(target)
            elif options.update:
                result=subprocess.run(['git','-C',str(target),'pull','--ff-only'],text=True,capture_output=True,timeout=90)
                if result.returncode:raise RuntimeError(result.stderr.strip())
            result=subprocess.run(['git','-C',str(target),'rev-parse','HEAD'],text=True,capture_output=True,check=True)
            revisions[spec['name']]=result.stdout.strip()
        except (OSError,RuntimeError,subprocess.SubprocessError) as exc:errors.append(spec['name']+': '+str(exc))
        finally:
            if stage.exists():shutil.rmtree(stage)
    fd,tmp=tempfile.mkstemp(dir=state,prefix='.revisions-')
    with os.fdopen(fd,'w') as f:json.dump(revisions,f,indent=2)
    os.replace(tmp,state/'pixel-plugin-revisions.json')
    print(json.dumps({'errors':errors,'revisions':revisions}))
    return bool(errors)
with open(state/'pixel-plugin-install.lock','a') as lock:
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:print('Another plugin installation is running',file=sys.stderr);sys.exit(1)
    sys.exit(install())
