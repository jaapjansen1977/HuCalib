import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from mocap_app.analysis.gaitdynamics_wsl import WslBackend, decode_output, DISTRIBUTION, PREFIX
from tools.setup_gaitdynamics import setup


class WslTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.calls = []

    def backend(self, status=0, text='', runner=None):
        def run(args, **kwargs):
            self.calls.append((args, kwargs))
            return subprocess.CompletedProcess(args, status, text)
        return WslBackend(runner=runner or run, state_dir=self.root / 'state')

    def test_localized_utf16_wsl_listing_and_readiness(self):
        def run(args, **kwargs):
            self.calls.append(args)
            output = '* Ubuntu-24.04   Gestopt   2\r\n' if '--list' in args else 'HU3D_READY\n'
            return subprocess.CompletedProcess(args, 0, output.encode('utf-16-le'))
        backend = self.backend(runner=run)
        with patch('mocap_app.analysis.gaitdynamics_wsl.sys.platform', 'win32'):
            self.assertEqual(backend.probe()['status'], 'ready')
        self.assertEqual(len(self.calls), 2)
        self.assertIn('--user', self.calls[1]) if '--user' in self.calls[1] else self.assertIn('-u', self.calls[1])
        self.assertIn('verify_runtime', self.calls[1][-1])

    def test_wsl1_is_not_changed_or_installed_over(self):
        backend = self.backend(text='* Ubuntu-24.04 Running 1\n')
        with patch('mocap_app.analysis.gaitdynamics_wsl.sys.platform', 'win32'):
            self.assertEqual(backend.install()['status'], 'unsupported')
        self.assertEqual(len(self.calls), 1)

    def test_first_install_requires_elevation_then_can_resume_after_restart(self):
        backend = self.backend()
        with patch.object(backend, 'probe', return_value={'status': 'install_required'}):
            result = backend.install()
        self.assertEqual(result['status'], 'restart_required')
        command = self.calls[0][0]
        self.assertEqual(command[0], 'powershell.exe')
        self.assertIn('-Verb RunAs', command[-1])
        self.assertIn('--no-distribution', command[-1])
        self.assertNotIn('--distribution', command[-1])
        self.assertNotIn('Restart-Computer', command[-1])
        self.assertEqual(json.loads((self.root / 'state/setup.json').read_text())['status'], 'restart_required')
        with patch.object(backend, 'probe', return_value={'status': 'ready', 'message': 'gereed'}):
            self.assertEqual(backend.install()['status'], 'ready')
        self.assertEqual(len(self.calls), 1)

    def test_denied_elevation_is_failure_and_not_readiness(self):
        backend = self.backend(status=1, text='The operation was canceled by the user')
        with patch.object(backend, 'probe', return_value={'status': 'install_required'}):
            with self.assertRaisesRegex(RuntimeError, 'toestemming'):
                backend.install()
        self.assertFalse((self.root / 'state/setup.json').exists())

    def test_existing_ubuntu_setup_preserves_other_environments_and_uses_cpu(self):
        backend = self.backend()
        with patch.object(backend, 'probe', side_effect=[{'status': 'environment_required'}, {'status': 'ready', 'message': 'gereed'}]), patch.object(backend, 'linux_path', return_value='/mnt/c/Temp/setup'):
            self.assertEqual(backend.install()['status'], 'ready')
        commands = [args for args, _ in self.calls]
        self.assertTrue(all(args[0] == 'wsl.exe' and DISTRIBUTION in args for args in commands))
        self.assertFalse(any('--unregister' in args or '--set-default' in args for args in commands))
        torch = next(args for args in commands if 'torch==2.8.0' in args)
        self.assertIn('https://download.pytorch.org/whl/cpu', torch)
        self.assertTrue(any(PREFIX + '/runtime' in args for args in commands))

    def test_distribution_is_installed_in_requesting_user_profile_without_elevation(self):
        backend = self.backend()
        with patch.object(backend, 'probe', side_effect=[{'status': 'distribution_required'}, {'status': 'environment_required'}, {'status': 'ready', 'message': 'gereed'}]), patch.object(backend, 'linux_path', return_value='/mnt/c/Temp/setup'):
            self.assertEqual(backend.install()['status'], 'ready')
        args = self.calls[0][0]
        self.assertEqual(args, ['wsl.exe', '--install', '--distribution', DISTRIBUTION, '--no-launch'])
        self.assertTrue(all(call[0][0] != 'powershell.exe' for call in self.calls))

    def test_older_wsl_client_that_rejects_install_version_option_can_install(self):
        def old_client(args, **kwargs):
            self.calls.append((args, kwargs))
            if '--install' in args and '--version' in args:
                return subprocess.CompletedProcess(args, 4294967295, 'Gebruik: wsl.exe [Opties]\n--set-default-version <Versie>')
            return subprocess.CompletedProcess(args, 0, '')
        backend = self.backend(runner=old_client)
        with patch.object(backend, 'probe', side_effect=[{'status': 'distribution_required'}, {'status': 'environment_required'}, {'status': 'ready', 'message': 'gereed'}]), patch.object(backend, 'linux_path', return_value='/mnt/c/Temp/setup'):
            self.assertEqual(backend.install()['status'], 'ready')
        self.assertNotIn('--version', self.calls[0][0])

    def test_new_distribution_on_wsl1_is_converted_without_changing_global_default(self):
        backend = self.backend()
        with patch.object(backend, 'probe', side_effect=[{'status': 'distribution_required'}, {'status': 'unsupported'}, {'status': 'environment_required'}, {'status': 'ready', 'message': 'gereed'}]), patch.object(backend, 'linux_path', return_value='/mnt/c/Temp/setup'):
            self.assertEqual(backend.install()['status'], 'ready')
        self.assertEqual(self.calls[1][0], ['wsl.exe', '--set-version', DISTRIBUTION, '2'])
        self.assertFalse(any('--set-default-version' in call[0] or '--shutdown' in call[0] for call in self.calls))

    def test_spaces_and_shell_metacharacters_are_passed_as_one_path_argument(self):
        backend = self.backend(text='/mnt/c/example')
        path = self.root / "ruimte ' & $(whoami) — motion.mot"
        self.assertEqual(backend.linux_path(path), '/mnt/c/example')
        args, _ = self.calls[0]
        self.assertEqual(args[-1], str(path.absolute()))
        self.assertEqual(args[-4:-1], ['wslpath', '-a', '-u'])
        self.assertNotIn('bash', args)

    def test_analysis_failure_reports_output_location_without_creating_success(self):
        messages = []
        backend = self.backend()
        backend.notify = messages.append
        with patch.object(backend, 'probe', return_value={'status': 'ready'}), patch.object(backend, 'linux_path', side_effect=lambda p: str(p)), patch.object(backend, '_linux', side_effect=RuntimeError('nimble failed')), patch('mocap_app.analysis.gaitdynamics.inspect_inputs', return_value={'compatible': True}):
            with self.assertRaisesRegex(RuntimeError, 'nimble failed'):
                backend.analyze(self.root / 'motion.mot', self.root / 'model.osim', self.root / 'output', 1.75, 70, 0)
        self.assertTrue(any('gaitdynamics.log' in text for text in messages))
        self.assertFalse((self.root / 'output/windows-transport.json').exists())

    def test_verified_downloads_resume_but_corrupt_files_are_not_overwritten(self):
        source, license_data = b'verified source', b'verified license'
        root = self.root / 'runtime'
        root.mkdir()
        (root / 'gait_dynamics.py').write_bytes(source)
        (root / 'LICENSE').write_bytes(license_data)
        checksum = lambda data: hashlib.sha256(data).hexdigest()
        with patch('tools.setup_gaitdynamics.SOURCE_SHA256', checksum(source)), patch('tools.setup_gaitdynamics.MODEL_HASHES', {}), patch('tools.setup_gaitdynamics.urllib.request.urlopen') as network:
            # Existing license uses the real pinned checksum: mismatches block a resume.
            with self.assertRaisesRegex(ValueError, 'LICENSE'):
                setup(root)
            network.assert_not_called()
        self.assertEqual((root / 'LICENSE').read_bytes(), license_data)
        self.assertEqual(decode_output(b'\xff\xfe' + 'tekst'.encode('utf-16-le')), 'tekst')


if __name__ == '__main__':
    unittest.main()
