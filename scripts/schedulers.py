"""Per-user scheduler backends. No elevated privileges or passwords are requested."""
from __future__ import annotations

import csv
import io
import os
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET

LABEL = 'com.rrpauls.sports-betting-expert-updater'
UNIT = 'sports-betting-expert-updater'
NS = 'http://schemas.microsoft.com/windows/2004/02/mit/task'


def call(runner, args, *, check=True):
    return runner(args, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def systemd_quote(value: str, *, expand_environment: bool = True) -> str:
    if any(c in value for c in '\n\r\x00'):
        raise ValueError('newline/NUL in scheduler argument')
    # systemd performs specifier and environment expansion even within quotes.
    value = value.replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%')
    if expand_environment:
        value = value.replace('$', '$$')
    return '"' + value + '"'


def write_systemd(home: Path, command: list[str], codex_home: Path) -> Path:
    folder = home / '.config/systemd/user'
    folder.mkdir(parents=True, exist_ok=True)
    service = ('[Unit]\nDescription=Sports Betting Expert validated update\n'
               '[Service]\nType=oneshot\n'
               'Environment=' + systemd_quote(f'CODEX_HOME={codex_home}', expand_environment=False) + '\n'
               'ExecStart=' + ' '.join(map(systemd_quote, command)) + '\n')
    (folder / f'{UNIT}.service').write_text(service, encoding='utf-8')
    timer = folder / f'{UNIT}.timer'
    timer.write_text('[Unit]\nDescription=Daily Sports Betting Expert update\n'
                     '[Timer]\nOnStartupSec=5m\nOnUnitActiveSec=1d\n'
                     '[Install]\nWantedBy=timers.target\n', encoding='utf-8')
    return timer


def task_xml(command: list[str], user: str) -> bytes:
    ET.register_namespace('', NS)
    def child(parent, tag, text=None, **attrs):
        element = ET.SubElement(parent, f'{{{NS}}}{tag}', attrs)
        element.text = text
        return element
    root = ET.Element(f'{{{NS}}}Task', {'version': '1.2'})
    triggers = child(root, 'Triggers')
    logon = child(triggers, 'LogonTrigger')
    repetition = child(logon, 'Repetition')
    child(repetition, 'Interval', 'P1D')
    child(repetition, 'StopAtDurationEnd', 'false')
    child(logon, 'Enabled', 'true')
    child(logon, 'UserId', user)
    principals = child(root, 'Principals')
    principal = child(principals, 'Principal', id='Author')
    child(principal, 'UserId', user)
    child(principal, 'LogonType', 'InteractiveToken')
    child(principal, 'RunLevel', 'LeastPrivilege')
    settings = child(root, 'Settings')
    child(settings, 'MultipleInstancesPolicy', 'IgnoreNew')
    child(settings, 'DisallowStartIfOnBatteries', 'false')
    child(settings, 'StopIfGoingOnBatteries', 'false')
    child(settings, 'StartWhenAvailable', 'true')
    child(settings, 'Enabled', 'true')
    child(settings, 'ExecutionTimeLimit', 'PT1H')
    actions = child(root, 'Actions', Context='Author')
    action = child(actions, 'Exec')
    child(action, 'Command', command[0])
    child(action, 'Arguments', subprocess.list2cmdline(command[1:]))
    return ET.tostring(root, encoding='utf-16', xml_declaration=True)


def state_root(home: Path, platform: str) -> Path:
    if platform == 'darwin':
        return home / 'Library/Application Support/Sports Betting Expert Updater'
    if platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', str(home / 'AppData/Local'))) / 'Sports Betting Expert Updater'
    if platform.startswith('linux'):
        return home / '.local/share/sports-betting-expert-updater'
    raise RuntimeError(f'unsupported scheduler platform: {platform}')


def scheduler_status(platform: str, runner=subprocess.run) -> bool:
    if platform.startswith('linux'):
        return call(runner, ['systemctl', '--user', 'is-enabled', f'{UNIT}.timer'], check=False).returncode == 0 and call(
            runner, ['systemctl', '--user', 'is-active', f'{UNIT}.timer'], check=False).returncode == 0
    if platform == 'win32':
        result = call(runner, ['schtasks', '/Query', '/TN', LABEL, '/XML'], check=False)
        if result.returncode != 0:
            print(f"DEBUG: schtasks query failed. Code: {result.returncode}")
            print(f"DEBUG STDOUT: {repr(result.stdout)}")
            print(f"DEBUG STDERR: {repr(result.stderr)}")
            return False
        try:
            root = ET.fromstring(result.stdout)
        except Exception as e:
            print(f"DEBUG PARSE ERROR: {e}")
            print(f"DEBUG STDOUT: {repr(result.stdout)}")
            raise
        return root.findtext(f'{{{NS}}}Settings/{{{NS}}}Enabled') == 'true'
    raise RuntimeError(f'unsupported scheduler platform: {platform}')


def install_scheduler(platform: str, home: Path, command: list[str], codex_home: Path,
                      runner=subprocess.run) -> Path:
    if platform.startswith('linux'):
        target = write_systemd(home, command, codex_home)
        call(runner, ['systemctl', '--user', 'daemon-reload'])
        call(runner, ['systemctl', '--user', 'enable', '--now', f'{UNIT}.timer'])
    elif platform == 'win32':
        # Use the actual signed-in user's SID, including domain accounts.
        identity = call(runner, ['whoami', '/user', '/fo', 'csv', '/nh']).stdout
        user = next(csv.reader(io.StringIO(identity.strip())))[1]
        target = state_root(home, platform) / f'{LABEL}.xml'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(task_xml(command, user))
        call(runner, ['schtasks', '/Create', '/TN', LABEL, '/XML', str(target), '/F'])
    else:
        raise RuntimeError(f'unsupported scheduler platform: {platform}')
    if not scheduler_status(platform, runner):
        raise RuntimeError('scheduler registration was not verified')
    return target


def uninstall_scheduler(platform: str, home: Path, runner=subprocess.run) -> None:
    if platform.startswith('linux'):
        folder = home / '.config/systemd/user'
        if (folder / f'{UNIT}.timer').exists():
            call(runner, ['systemctl', '--user', 'disable', '--now', f'{UNIT}.timer'])
            for suffix in ('timer', 'service'):
                (folder / f'{UNIT}.{suffix}').unlink(missing_ok=True)
            call(runner, ['systemctl', '--user', 'daemon-reload'])
    elif platform == 'win32':
        result = call(runner, ['schtasks', '/Query', '/TN', LABEL], check=False)
        if result.returncode == 0:
            call(runner, ['schtasks', '/Delete', '/TN', LABEL, '/F'])
    else:
        raise RuntimeError(f'unsupported scheduler platform: {platform}')
