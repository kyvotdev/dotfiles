import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'config/pixel-shell'))
import calendar_app
class CalendarConfigTests(unittest.TestCase):
    def test_gtk3_api_and_stylesheet(self):calendar_app.check_configuration()
    def test_bad_palette_does_not_prevent_startup(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'palette.json';path.write_text('broken')
            self.assertEqual(calendar_app.load_palette(path),calendar_app.DEFAULT_PALETTE)
            path.write_text('{"accent":"invalid CSS", "bg":"#121212"}')
            palette=calendar_app.load_palette(path)
            self.assertEqual(palette['accent'],calendar_app.DEFAULT_PALETTE['accent'])
            self.assertEqual(palette['bg'],'#121212')
if __name__=='__main__':unittest.main()
