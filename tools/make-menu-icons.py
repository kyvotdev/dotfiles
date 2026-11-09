#!/usr/bin/env python3
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]/'config/pixel-shell/icons'
root.mkdir(exist_ok=True)
paths={
'wifi':'<path d="M3 9a14 14 0 0 1 18 0M6 12a9 9 0 0 1 12 0M9 15a4 4 0 0 1 6 0"/><circle cx="12" cy="19" r="1"/>',
'bt':'<path d="M7 6l10 12-5 4V2l5 4L7 18"/>',
'power':'<path d="M12 2v9M7 5a9 9 0 1 0 10 0"/>',
'lock':'<rect x="5" y="10" width="14" height="11" rx="1"/><path d="M8 10V6a4 4 0 0 1 8 0v4M12 14v3"/>',
'screen':'<rect x="2" y="3" width="20" height="14"/><path d="M8 21h8M12 17v4"/>',
'sound':'<path d="M3 9h4l5-5v16l-5-5H3zM16 8a6 6 0 0 1 0 8M19 5a10 10 0 0 1 0 14"/>',
'moon':'<path d="M20 15A9 9 0 0 1 9 3a9 9 0 1 0 11 12z"/>',
'refresh':'<path d="M20 8a9 9 0 0 0-15-3L2 8m0-6v6h6M4 16a9 9 0 0 0 15 3l3-3m0 6v-6h-6"/>',
'settings':'<path d="M3 6h18M3 12h18M3 18h18"/><rect x="6" y="3" width="4" height="6"/><rect x="14" y="9" width="4" height="6"/><rect x="7" y="15" width="4" height="6"/>',
'image':'<rect x="3" y="3" width="18" height="18"/><path d="M3 17l5-5 4 4 4-6 5 7"/><circle cx="8" cy="8" r="1"/>',
'check':'<path d="M4 12l5 5L20 6"/>',
'calendar':'<rect x="3" y="5" width="18" height="16"/><path d="M7 2v6M17 2v6M3 10h18M7 14h2M12 14h2M17 14h1M7 18h2M12 18h2"/>',
'bell':'<path d="M5 16V10a7 7 0 0 1 14 0v6l2 2H3zM9 21h6"/>',
'note':'<path d="M4 2h12l4 4v16H4zM15 2v5h5M8 11h8M8 15h8M8 19h5"/>',
 'timer':'<circle cx="12" cy="14" r="8"/><path d="M9 2h6M12 2v4M12 9v5l3 2M18 5l2 2"/>',
'folder':'<path d="M2 5h8l2 3h10v13H2z"/>',
'shuffle':'<path d="M3 6h3c5 0 7 12 12 12h3m-4-4 4 4-4 4M3 18h3c5 0 7-12 12-12h3m-4-4 4 4-4 4"/>',
'next':'<path d="M8 5l7 7-7 7"/>',
'prev':'<path d="M16 5l-7 7 7 7"/>',
'cancel':'<path d="M5 5l14 14M5 19L19 5"/>',
'copy':'<rect x="8" y="8" width="13" height="13"/><path d="M16 8V3H3v13h5"/>',
'trash':'<path d="M3 6h18M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7M14 10v7"/>',
'link':'<path d="M10 7l3-3a5 5 0 0 1 7 7l-3 3M14 17l-3 3a5 5 0 0 1-7-7l3-3M8 16l8-8"/>',
'unlink':'<path d="M14 7l2-2a4 4 0 0 1 6 6l-2 2M10 17l-2 2a4 4 0 0 1-6-6l2-2M3 3l18 18"/>'}
state=Path.home()/'.local/state/pixel-shell/palette.json'
accent=json.loads(state.read_text()).get('accent','#80b7db') if state.exists() else '#80b7db'
for name,content in paths.items():
    (root/(name+'.svg')).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{accent}" stroke-width="1.8" stroke-linecap="square" stroke-linejoin="miter">{content}</svg>\n')
