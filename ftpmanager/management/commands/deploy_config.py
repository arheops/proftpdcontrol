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
            help='Restart ProFTPD service after deploying'
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

    def handle(self, *args, **options):
        config_dir = options['config_dir']
        config_path = os.path.join(config_dir, options['config_file'])
        passwd_path = os.path.join(config_dir, options['passwd_file'])
        dry_run = options['dry_run']

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

        # Ensure directories exist
        config_file_dir = os.path.dirname(config_path)
        if not os.path.exists(config_file_dir):
            self.stdout.write(f'Creating directory: {config_file_dir}')
            os.makedirs(config_file_dir, mode=0o755)

        # Write config file
        self.stdout.write(f'Writing config to: {config_path}')
        try:
            with open(config_path, 'w') as f:
                f.write(config_content)
            os.chmod(config_path, 0o644)
        except PermissionError:
            raise CommandError(f'Permission denied writing to {config_path}. Run with sudo.')

        # Write passwd file
        self.stdout.write(f'Writing passwd to: {passwd_path}')
        try:
            with open(passwd_path, 'w') as f:
                f.write(passwd_content)
            os.chmod(passwd_path, 0o600)
        except PermissionError:
            raise CommandError(f'Permission denied writing to {passwd_path}. Run with sudo.')

        self.stdout.write(self.style.SUCCESS('Configuration files deployed successfully.'))

        # Test configuration
        if options['test']:
            self.stdout.write('Testing ProFTPD configuration...')
            result = subprocess.run(['proftpd', '-t'], capture_output=True, text=True)
            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS('Configuration test passed.'))
            else:
                self.stdout.write(self.style.ERROR(f'Configuration test failed:\n{result.stderr}'))
                return

        # Restart service
        if options['restart']:
            self.stdout.write('Restarting ProFTPD service...')
            result = subprocess.run(['systemctl', 'restart', 'proftpd'], capture_output=True, text=True)
            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS('ProFTPD service restarted.'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to restart ProFTPD:\n{result.stderr}'))
