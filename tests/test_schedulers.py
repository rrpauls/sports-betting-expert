import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
from scripts import schedulers, install_updater


class SchedulerTests(unittest.TestCase):
    def test_linux_install_status_uninstall(self):
        calls = []
        def runner(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, 'active', '')
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            command = ['/path with spaces/python', '/scripts/update.py', '--codex', '/path/codex']
            timer = schedulers.install_scheduler('linux', home, command, home / '.codex', runner)
            self.assertTrue(timer.exists())
            service = timer.with_suffix('.service').read_text()
            self.assertIn('"/path with spaces/python"', service)
            self.assertTrue(schedulers.scheduler_status('linux', runner))
            schedulers.uninstall_scheduler('linux', home, runner)
            self.assertFalse(timer.exists())
        self.assertIn(['systemctl', '--user', 'enable', '--now', f'{schedulers.UNIT}.timer'], calls)
        self.assertIn(['systemctl', '--user', 'disable', '--now', f'{schedulers.UNIT}.timer'], calls)

    def test_windows_task_install_status_uninstall(self):
        calls = []
        command = [r'C:\User Files\python.exe', r'C:\User Files\update.py', '--codex', r'C:\Tools\codex.exe']
        document = schedulers.task_xml(command, 'S-1-5-21-123')
        def runner(args, **kwargs):
            calls.append(args)
            output = '"user","S-1-5-21-123"' if args[0] == 'whoami' else document.decode('utf-16')
            return subprocess.CompletedProcess(args, 0, output, '')
        with tempfile.TemporaryDirectory() as directory, patch.dict('os.environ', {'LOCALAPPDATA': directory}):
            target = schedulers.install_scheduler('win32', Path(directory), command, Path(directory), runner)
            self.assertEqual(target.read_bytes(), document)
            self.assertTrue(schedulers.scheduler_status('win32', runner))
            schedulers.uninstall_scheduler('win32', Path(directory), runner)
        root = ET.fromstring(document)
        ns = {'t': schedulers.NS}
        self.assertEqual(root.findtext('t:Principals/t:Principal/t:RunLevel', namespaces=ns), 'LeastPrivilege')
        self.assertEqual(root.findtext('t:Principals/t:Principal/t:LogonType', namespaces=ns), 'InteractiveToken')
        self.assertEqual(root.findtext('t:Actions/t:Exec/t:Command', namespaces=ns), command[0])
        self.assertEqual(root.findtext('t:Actions/t:Exec/t:Arguments', namespaces=ns), subprocess.list2cmdline(command[1:]))
        self.assertIn(['schtasks', '/Delete', '/TN', schedulers.LABEL, '/F'], calls)

    def test_failed_registration_is_not_reported_as_success(self):
        def runner(command, **kwargs):
            return subprocess.CompletedProcess(command, 1 if 'is-enabled' in command else 0, '', '')
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(RuntimeError):
            schedulers.install_scheduler('linux', Path(directory), ['python', 'updater'], Path(directory), runner)

    def test_unit_quoting_prevents_variable_and_specifier_expansion(self):
        self.assertEqual(schedulers.systemd_quote('a%h$USER"b'), '"a%%h$$USER\\"b"')
        with self.assertRaises(ValueError):
            schedulers.systemd_quote('argument\nExecStart=bad')

    def test_dedicated_runtime_fresh_install_is_self_contained(self):
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            # Exercise venv creation and imports; skip network dependency installation.
            with patch.object(install_updater.subprocess, 'run'):
                python = install_updater._ensure_runtime(source, state, Path(__import__('sys').executable))
            result = subprocess.run([str(python), str(state / 'scripts/update_plugin.py'), '--help'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((state / 'plugin.json').exists())
            self.assertTrue((state / 'scripts/schedulers.py').exists())
