#!/usr/bin/env python3
"""Generate the complete key reference from the active niri binding files."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DESCRIPTIONS={
'focus-column-left':'Фокус на колонке слева','focus-column-right':'Фокус на колонке справа','focus-window-down':'Фокус на окне ниже','focus-window-up':'Фокус на окне выше','move-column-left':'Переместить колонку влево','move-column-right':'Переместить колонку вправо','move-window-up':'Переместить окно вверх','move-window-down':'Переместить окно вниз','focus-column-first':'Первая колонка','focus-column-last':'Последняя колонка','move-column-to-first':'Перенести колонку в начало','move-column-to-last':'Перенести колонку в конец','focus-workspace-down':'Следующее рабочее пространство','focus-workspace-up':'Предыдущее рабочее пространство','move-column-to-workspace-down':'Перенести колонку на следующее пространство','move-column-to-workspace-up':'Перенести колонку на предыдущее пространство','move-workspace-down':'Переместить рабочее пространство вниз','move-workspace-up':'Переместить рабочее пространство вверх','consume-or-expel-window-left':'Объединить / отделить окно слева','consume-or-expel-window-right':'Объединить / отделить окно справа','consume-window-into-column':'Добавить соседнее окно в колонку','expel-window-from-column':'Отделить нижнее окно в колонку','switch-preset-column-width':'Следующая ширина колонки','switch-preset-column-width-back':'Предыдущая ширина колонки','switch-preset-window-height':'Следующая высота окна','reset-window-height':'Сбросить высоту окна','maximize-column':'Развернуть колонку','fullscreen-window':'Полноэкранный режим','maximize-window-to-edges':'Развернуть окно до краёв','expand-column-to-available-width':'Занять свободную ширину','center-column':'Центрировать колонку','center-visible-columns':'Центрировать видимые колонки','toggle-window-floating':'Плавающий / плиточный режим','switch-focus-between-floating-and-tiling':'Переключить фокус между плавающими и плиточными окнами','toggle-column-tabbed-display':'Вкладки / стопка в колонке','screenshot':'Снимок выбранной области','screenshot-screen':'Снимок экрана','screenshot-window':'Снимок окна','toggle-overview':'Обзор окон','close-window':'Закрыть окно','quit':'Выйти из niri с подтверждением','show-hotkey-overlay':'Подсказка сочетаний','toggle-keyboard-shortcuts-inhibit':'Разрешить / запретить перехват горячих клавиш приложением','power-off-monitors':'Погасить мониторы; любой ввод включает их снова'}
def describe(action):
    if action=='spawn "fuzzel"':return 'Запуск приложения'
    first=action.split()[0]
    if first in DESCRIPTIONS:return DESCRIPTIONS[first]
    for marker,label in [('pixel-displays" "rescue','Включить экраны и восстановить автоматическое расположение'),('pixel-displays','Мониторы / HDMI / дублирование'),('pixel-caffeine','Caffeine'),('pixel-terminal','Терминал: Kitty / fish / Starship'),('pixel-wallpaper','Выбор обоев'),('pixel-extras" "calendar','Календарь и заметки'),('pixel-extras" "notifications','Центр уведомлений'),('pixel-extras" "timer','Таймер'),('"makoctl" "restore','Вернуть последнее уведомление'),('zen-browser','Zen Browser'),('telegram-desktop','Telegram'),('pixel-bluetooth','Bluetooth'),('pixel-control" "menu','Центр управления'),('pixel-control" "wifi','Wi-Fi'),('pixel-control" "hotspot','Хотспот'),('pixel-control" "audio','Аудиоустройства'),('pixel-control" "power','Питание'),('swaylock','Блокировка экрана'),('orca','Переключить экранный диктор')]:
        if marker in action:return label
    if 'wpctl' in action:
        if 'SOURCE' in action:return 'Включить / выключить микрофон'
        if 'set-mute' in action:return 'Включить / выключить звук'
        return 'Громкость '+('+3%' if '0.03+' in action else '−3%')
    if 'brightnessctl' in action:return 'Яркость '+('+5%' if '+5%' in action else '−5%, минимум 1')
    if 'playerctl' in action:return 'Медиаплеер: '+action.split('playerctl',1)[1].strip(' "')
    if first.startswith('focus-monitor-'):return 'Фокус на мониторе: '+first.removeprefix('focus-monitor-')
    if first.startswith('move-column-to-monitor-'):return 'Перенести колонку на монитор: '+first.removeprefix('move-column-to-monitor-')
    if first=='focus-workspace':return 'Открыть рабочее пространство '+action.split()[-1]
    if first=='move-column-to-workspace':return 'Перенести колонку на пространство '+action.split()[-1]
    if first=='set-column-width':return 'Ширина колонки '+action.split()[-1].strip('"')
    if first=='set-window-height':return 'Высота окна '+action.split()[-1].strip('"')
    return action
bindings={}
for relative in ('config/niri/config.kdl','config/niri/pixel-shell.kdl'):
    for line in (ROOT/relative).read_text().splitlines():
        match=re.match(r'\s*([A-Za-z0-9_]+(?:\+[A-Za-z0-9_]+)*)\b[^{}]*\{\s*(.*?)\s*;\s*\}\s*$',line)
        if not match:continue
        key,action=match.groups()
        if '+' not in key and key!='Print' and not key.startswith('XF86'):continue
        key=key.replace('Mod+','Win+').replace('Super+','Win+').replace('Return','Enter')
        bindings[key]=action
groups={}
for key,action in bindings.items():groups.setdefault(action,[]).append(key)
text='## Все сочетания niri\n\nWin = Super; Alt+Shift переключает US/RU через XKB. Таблица сгенерирована из конфигов; обновление: `python3 tools/update-hotkeys.py`.\n\n| Клавиши | Действие |\n| --- | --- |\n'
for action,keys in groups.items():text+='| '+', '.join('`'+k+'`' for k in keys)+' | '+describe(action).replace('|','\\|')+' |\n'
(ROOT/'docs/HOTKEYS.md').write_text('# Сочетания клавиш\n\n'+text)
readme=ROOT/'README.md'
if readme.exists():
    old=readme.read_text();start='<!-- HOTKEYS:START -->';end='<!-- HOTKEYS:END -->'
    if start in old and end in old:
        before,rest=old.split(start,1);_,after=rest.split(end,1);readme.write_text(before+start+'\n'+text+'\n'+end+after)
print(f'Documented {len(bindings)} bindings in {len(groups)} rows.')
