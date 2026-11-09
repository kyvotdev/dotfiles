import sys, unittest, tempfile, types, colorsys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'config/pixel-shell'))
import control, theme, bluetooth, extras, wallpaper, common
class SampleImage:
    def __init__(self, pixels): self.pixels=pixels
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def convert(self,mode): return self
    def thumbnail(self,size): pass
    def getdata(self): return self.pixels
class ShellTests(unittest.TestCase):
    def test_nmcli_escaped_fields(self):
        self.assertEqual(control.fields(r'*:Cafe\: Guest:82:WPA2'),['*','Cafe: Guest','82','WPA2'])
        self.assertEqual(control.fields(r'a\\b:c'),['a\\b','c'])
    def test_palette_excludes_green_and_red(self):
        for pixels in ([(0,255,0,255)]*20,[(255,0,0,255)]*20,[(0,140,255,255)]*20,[(0,0,0,255)]*20):
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'test.png'; path.write_bytes(b'input')
                pil=types.ModuleType('PIL'); pil.Image=types.SimpleNamespace(open=lambda _:SampleImage(pixels))
                with patch.dict(sys.modules,{'PIL':pil}): palette=theme.palette(path)
                for key in ('accent','accent2'):
                    c=palette[key]; rgb=[int(c[i:i+2],16)/255 for i in (1,3,5)]
                    self.assertTrue(.52<=colorsys.rgb_to_hsv(*rgb)[0]<=.69,palette)
                def luminance(color):
                    channels=[int(color[i:i+2],16)/255 for i in (1,3,5)]
                    channels=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in channels]
                    return sum(x*w for x,w in zip(channels,(.2126,.7152,.0722)))
                self.assertGreater((luminance(palette['fg'])+.05)/(luminance(palette['bg'])+.05),7)
    def test_menu_icons_preserve_selection_and_clean_labels(self):
        fake=types.SimpleNamespace(returncode=0,stdout='1\n')
        rows=[(common.IC['wifi']+'  Network','wifi'),('Disconnect\nnow','disconnect')]
        with patch.object(common.subprocess,'run',return_value=fake) as call:
            self.assertEqual(common.choose('Network',rows),'disconnect')
        data=call.call_args.kwargs['input'].splitlines()
        self.assertEqual(len(data),2)
        self.assertIn('Network\0icon\x1f',data[0])
        self.assertTrue(data[1].endswith('/icons/unlink.svg'))
    def test_calendar_year_boundaries(self):
        self.assertEqual(extras.shift_month(2026,12,1),(2027,1))
        self.assertEqual(extras.shift_month(2026,1,-1),(2025,12))
        self.assertIn(' 29 ',extras.calendar_text(2028,2))
        self.assertNotIn(' 29 ',extras.calendar_text(2027,2))
    def test_wallpaper_cycle(self):
        paths=[Path('/a.png'),Path('/b.png')]
        self.assertEqual(wallpaper.next_wallpaper(paths,paths[-1]),paths[0])
        self.assertEqual(wallpaper.next_wallpaper(paths,None),paths[0])
        self.assertIsNone(wallpaper.next_wallpaper([],None))
    def test_passkey_validation(self):
        class Stub:
            def __init__(self,value): self.value=value
            def ask(self,*a,**k): return self.value
        for value in ('0','000123','999999'):
            self.assertEqual(int(bluetooth.Agent.RequestPasskey(Stub(value),'/device')),int(value))
        for value in ('','1000000','123x','-1','١٢٣'):
            with self.assertRaises(bluetooth.Rejected): bluetooth.Agent.RequestPasskey(Stub(value),'/device')
    def test_atomic_writes_preserve_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            actual=Path(tmp)/'actual';actual.write_text('before')
            link=Path(tmp)/'link';link.symlink_to(actual)
            theme.write(link,'after')
            self.assertTrue(link.is_symlink());self.assertEqual(actual.read_text(),'after')
if __name__=='__main__': unittest.main()
