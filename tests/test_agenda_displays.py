import json,os,sys,tempfile,unittest,types
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'config/pixel-shell'))
from agenda import Agenda
import displays,common
class AgendaTests(unittest.TestCase):
    def test_legacy_notes_survive_edit_and_undo(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'notes.json';path.write_text(json.dumps({'2026-11-09':['Keep this note']}))
            agenda=Agenda(path);old=agenda.read()['2026-11-09'][0]
            self.assertEqual(old['id'],agenda.read()['2026-11-09'][0]['id'])
            agenda.update('2026-11-09',old['id'],done=True)
            item=agenda.remove('2026-11-09',old['id']);agenda.restore('2026-11-09',item)
            agenda.restore('2026-11-09',item)
            self.assertEqual(len(agenda.read()['2026-11-09']),1)
            self.assertTrue(agenda.read()['2026-11-09'][0]['done'])
            self.assertEqual(path.stat().st_mode&0o777,0o600)
    def test_independent_clients_do_not_overwrite_each_other(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'notes.json';a,b=Agenda(path),Agenda(path)
            a.add('2026-12-31','First');b.add('2026-12-31','Second')
            self.assertEqual([n['text'] for n in a.read()['2026-12-31']],['First','Second'])
    def test_invalid_file_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'notes.json';path.write_text('broken')
            with self.assertRaises(ValueError):Agenda(path).add('2026-11-09','test')
            self.assertEqual(path.read_text(),'broken')
class DisplayTests(unittest.TestCase):
    def snapshot(self):
        return {'eDP-1':{'current_mode':0,'logical':{'x':0,'y':0,'width':1920,'height':1080,'scale':1,'transform':'Normal'},'modes':[{'width':1920,'height':1080,'refresh_rate':59940}]},'HDMI-A-1':{'current_mode':None,'logical':None,'modes':[]}}
    def test_restore_enables_screen_before_disabling_other(self):
        calls=[];data=self.snapshot()
        with patch.object(displays,'outputs',return_value=data),patch.object(displays,'command',side_effect=lambda *args,**kw:calls.append(args)):
            displays.restore(data)
        self.assertEqual(calls[0],('eDP-1','on'))
        self.assertIn(('eDP-1','mode','1920x1080@59.940'),calls)
        self.assertEqual(calls[-1],('HDMI-A-1','off'))
    def test_no_remaining_saved_screen_uses_connected_screen(self):
        calls=[]
        with patch.object(displays,'outputs',return_value={'DP-2':{}}),patch.object(displays,'command',side_effect=lambda *a,**k:calls.append(a)):
            displays.restore(self.snapshot())
        self.assertEqual(calls,[('DP-2','on')])
    def test_confirmation_timeout_returns_cancel(self):
        import subprocess
        with patch.object(common.subprocess,'run',side_effect=subprocess.TimeoutExpired('fuzzel',15)):
            self.assertIsNone(common.choose('Keep?', [('Keep',True)],timeout=15))
    def test_keep_and_reject_transaction(self):
        for answer in (True,False,None):
            with self.subTest(answer=answer),tempfile.TemporaryDirectory() as tmp:
                fake=types.SimpleNamespace(wait=lambda timeout:None)
                with patch.object(displays,'STATE',Path(tmp)),patch.object(displays,'outputs',return_value=self.snapshot()),patch.object(displays.subprocess,'Popen',return_value=fake),patch.object(displays,'choose',return_value=answer),patch.object(displays,'restore') as restore,patch.object(displays,'notify'):
                    displays.guarded_change(lambda snapshot:None)
                    self.assertEqual(restore.called,answer is not True)
if __name__=='__main__':unittest.main()
