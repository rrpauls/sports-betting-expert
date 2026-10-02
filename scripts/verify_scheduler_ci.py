"""Register/remove a temporary native scheduler running only a harmless local marker."""
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import schedulers


def main():
    token = uuid.uuid4().hex
    # Avoid touching a real updater installed by the CI user.
    schedulers.LABEL += '-ci-' + token
    schedulers.UNIT += '-ci-' + token
    home = Path.home()
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        marker = work / 'marker'
        script = work / 'marker.py'
        script.write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').touch()\n', encoding='utf-8')
        command = [sys.executable, str(script)]
        try:
            target = schedulers.install_scheduler(sys.platform, home, command, work / 'codex')
            if not schedulers.scheduler_status(sys.platform):
                raise RuntimeError('native scheduler not registered')
            if sys.platform.startswith('linux'):
                subprocess.run(['systemctl', '--user', 'start', schedulers.UNIT + '.service'], check=True)
                if not marker.exists():
                    raise RuntimeError('native service did not execute its marker')
            # Windows registration does not require a logged-in interactive session;
            # actual firing is verified by users at login, not assumed on a service runner.
        finally:
            schedulers.uninstall_scheduler(sys.platform, home)
            if sys.platform == 'win32':
                (schedulers.state_root(home, sys.platform) / f'{schedulers.LABEL}.xml').unlink(missing_ok=True)
        if schedulers.scheduler_status(sys.platform):
            raise RuntimeError('native scheduler remains after uninstall')
        print('Native scheduler registration/status/removal passed')


if __name__ == '__main__':
    main()
