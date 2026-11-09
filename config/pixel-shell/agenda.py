"""Private, atomic agenda storage with migration from the original notes format."""
import datetime as dt, fcntl, json, os, tempfile, uuid
from contextlib import contextmanager
from pathlib import Path
class Agenda:
    def __init__(self,path=None):self.path=Path(path or Path.home()/'.local/state/pixel-shell/notes.json')
    def read(self):
        if not self.path.exists():return {}
        data=json.loads(self.path.read_text())
        if not isinstance(data,dict):raise ValueError('Invalid agenda file; the original file was preserved')
        result={}
        for day,items in data.items():
            dt.date.fromisoformat(day)
            if not isinstance(items,list):raise ValueError('Invalid notes list')
            result[day]=[]
            for i,item in enumerate(items):
                if isinstance(item,str):item={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,day+':'+str(i)+':'+item)),'text':item,'done':False}
                if not isinstance(item,dict) or not isinstance(item.get('text'),str) or not isinstance(item.get('id'),str):raise ValueError('Invalid note entry')
                result[day].append(dict(item))
        return result
    @contextmanager
    def edit(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with open(self.path.with_suffix('.lock'),'a') as lock:
            os.chmod(lock.name,0o600);fcntl.flock(lock,fcntl.LOCK_EX)
            data=self.read();yield data
            fd,tmp=tempfile.mkstemp(dir=self.path.parent,prefix='.agenda-')
            try:
                with os.fdopen(fd,'w') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
                os.replace(tmp,self.path)
            finally:
                if os.path.exists(tmp):os.unlink(tmp)
    def add(self,day,text):
        dt.date.fromisoformat(day)
        if not text.strip():raise ValueError('Note is empty')
        item={'id':str(uuid.uuid4()),'text':text.strip(),'done':False}
        with self.edit() as data:data.setdefault(day,[]).append(item)
        return item
    def update(self,day,ident,**changes):
        with self.edit() as data:
            for item in data.get(day,[]):
                if item['id']==ident:
                    item.update({k:v for k,v in changes.items() if k in ('text','done')});return
            raise ValueError('This note was changed in another window; refresh the calendar')
    def remove(self,day,ident):
        with self.edit() as data:
            items=data.get(day,[])
            for i,item in enumerate(items):
                if item['id']==ident:return items.pop(i)
            raise ValueError('This note was already removed')
    def restore(self,day,item):
        with self.edit() as data:
            if not any(x['id']==item['id'] for x in data.get(day,[])):data.setdefault(day,[]).append(item)
