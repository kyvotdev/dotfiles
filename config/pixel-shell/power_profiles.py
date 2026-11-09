#!/usr/bin/env python3
"""Power profiles menu using the existing power-profiles-daemon service."""
import argparse
import json
import dbus
from common import choose, guarded, notify

SERVICE = 'net.hadess.PowerProfiles'
PATH = '/net/hadess/PowerProfiles'
LABELS = {
    'power-saver': ('Power saver', 'Longer battery life · reduced performance'),
    'balanced': ('Balanced', 'Automatic balance of power and performance'),
    'performance': ('Performance', 'Higher performance · more power and heat'),
}


def connect():
    bus = dbus.SystemBus()
    return dbus.Interface(bus.get_object(SERVICE, PATH), 'org.freedesktop.DBus.Properties')


def snapshot(props):
    data = props.GetAll(SERVICE)
    available = [str(p['Profile']) for p in data['Profiles']]
    return str(data['ActiveProfile']), available, data


def apply(props, target):
    current, available, data = snapshot(props)
    if target not in available:
        raise ValueError(f'{target} is not available on this device')
    inhibited = str(data.get('PerformanceInhibited', ''))
    if target == 'performance' and inhibited:
        raise ValueError(f'Performance mode is unavailable: {inhibited}')
    if current != target:
        props.Set(SERVICE, 'ActiveProfile', dbus.String(target))
    active, _, data = snapshot(props)
    if active != target:
        raise ValueError(f'Requested {target}, but the active profile is {active}')
    details = LABELS[target][1]
    degraded = str(data.get('PerformanceDegraded', ''))
    if target == 'performance' and degraded:
        details += f'\nPerformance limited: {degraded}'
    holds = data.get('ActiveProfileHolds', [])
    if holds:
        details += '\nActive application requests: ' + ', '.join(
            str(h.get('ApplicationId', 'Unknown application')) for h in holds)
    notify('Power mode · ' + LABELS[target][0], details)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', default='menu', choices=['menu', 'status', 'waybar', *LABELS])
    args = parser.parse_args()
    if args.action == 'waybar':
        try:
            current, _, data = snapshot(connect())
            icons = {'power-saver': '\U000f06a5', 'balanced': '\U000f0493', 'performance': '\U000f04c5'}
            short = {'power-saver': 'ECO', 'balanced': 'BAL', 'performance': 'PERF'}
            label, description = LABELS.get(current, (current, ''))
            tooltip = f'Power mode: {label}\n{description}\nClick to change mode'
            if data.get('PerformanceDegraded'):
                tooltip += '\nPerformance limited: ' + str(data['PerformanceDegraded'])
            output = {'text': icons.get(current, '\U000f0425') + ' ' + short.get(current, current),
                      'tooltip': tooltip, 'class': current}
        except (dbus.DBusException, OSError, ValueError) as error:
            output = {'text': '\U000f0425 ?', 'tooltip': 'Power profiles unavailable: ' + str(error),
                      'class': 'unavailable'}
        print(json.dumps(output))
        return
    props = connect()
    current, available, data = snapshot(props)
    if args.action == 'status':
        print(json.dumps({'active': current, 'available': available,
                          'performance_degraded': str(data.get('PerformanceDegraded', ''))}))
        return
    target = args.action
    if target == 'menu':
        rows = [(f'{LABELS[p][0]:<14}  {"[active]" if p == current else ""}', p)
                for p in LABELS if p in available]
        target = choose('Power mode', rows,
                        message='Power saver · Balanced · Performance\nCurrent: ' + LABELS.get(current, (current,))[0])
    if target:
        apply(props, target)


if __name__ == '__main__':
    guarded(main)
