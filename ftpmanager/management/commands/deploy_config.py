import os
import subprocess
from django.core.management.base import BaseCommand, CommandError
from ftpmanager.config_generator import generate_proftpd_config, generate_ftpusers_file


class Command(BaseCommand):
    help = 'Deploy ProFTPD configuration files to system directories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--config-dir',
            default='/etc/proftpd',
            help='ProFTPD configuration directory (default: /etc/proftpd)'
        )
        parser.add_argument(
            '--config-file',
            default='conf.d/users.conf',
            help='Config file path relative to config-dir (default: conf.d/users.conf)'
        )
        parser.add_argument(
            '--passwd-file',
            default='ftpd.passwd',
            help='Password file path relative to config-dir (default: ftpd.passwd)'
        )
        parser.add_argument(
            '--restart',
            action='store_true',
            help='Restart ProFTPD service after deploying (only if files changed)'
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test ProFTPD configuration after deploying'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force write even if content unchanged'
        )

    def read_file(self, path):
        """Read file content, return None if file doesn't exist"""
        try:
            with open(path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return None
        except PermissionError:
            raise CommandError(f'Permission denied reading {path}. Run with sudo.')

    def write_file(self, path, content, mode):
        """Write content to file and set permissions"""
        # Ensure directory exists
        file_dir = os.path.dirname(path)
        if not os.path.exists(file_dir):
            self.stdout.write(f'Creating directory: {file_dir}')
            os.makedirs(file_dir, mode=0o755)

        try:
            with open(path, 'w') as f:
                f.write(content)
            os.chmod(path, mode)
        except PermissionError:
            raise CommandError(f'Permission denied writing to {path}. Run with sudo.')

    def handle(self, *args, **options):
        config_dir = options['config_dir']
        config_path = os.path.join(config_dir, options['config_file'])
        passwd_path = os.path.join(config_dir, options['passwd_file'])
        dry_run = options['dry_run']
        force = options['force']

        # Generate configs
        self.stdout.write('Generating configuration files...')
        config_content = generate_proftpd_config()
        passwd_content = generate_ftpusers_file()

        if dry_run:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN MODE ===\n'))
            self.stdout.write(f'Would write config to: {config_path}')
            self.stdout.write(f'Would write passwd to: {passwd_path}')
            self.stdout.write('\n--- Config content ---')
            self.stdout.write(config_content)
            self.stdout.write('\n--- Passwd content ---')
            self.stdout.write(passwd_content)
            return

        # Read existing files
        existing_config = self.read_file(config_path)
        existing_passwd = self.read_file(passwd_path)

        # Track changes
        files_changed = False

        # Compare and write config file
        if force or existing_config != config_content:
            self.stdout.write(f'Writing config to: {config_path}')
            self.write_file(config_path, config_content, 0o644)
            files_changed = True
        else:
            self.stdout.write(f'Config unchanged: {config_path}')

        # Compare and write passwd file
        if force or existing_passwd != passwd_content:
            self.stdout.write(f'Writing passwd to: {passwd_path}')
            self.write_file(passwd_path, passwd_content, 0o600)
            files_changed = True
        else:
            self.stdout.write(f'Passwd unchanged: {passwd_path}')

        if files_changed:
            self.stdout.write(self.style.SUCCESS('Configuration files updated.'))
        else:
            self.stdout.write(self.style.SUCCESS('No changes detected.'))

        # Test configuration (always if requested)
        if options['test']:
            self.stdout.write('Testing ProFTPD configuration...')
            result = subprocess.run(['proftpd', '-t'], capture_output=True, text=True)
            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS('Configuration test passed.'))
            else:
                self.stdout.write(self.style.ERROR(f'Configuration test failed:\n{result.stderr}'))
                return

        # Restart service only if files changed
        if options['restart']:
            if files_changed:
                self.stdout.write('Restarting ProFTPD service...')
                result = subprocess.run(['systemctl', 'restart', 'proftpd'], capture_output=True, text=True)
                if result.returncode == 0:
                    self.stdout.write(self.style.SUCCESS('ProFTPD service restarted.'))
                else:
                    self.stdout.write(self.style.ERROR(f'Failed to restart ProFTPD:\n{result.stderr}'))
            else:
                self.stdout.write('Skipping restart: no files changed.')
