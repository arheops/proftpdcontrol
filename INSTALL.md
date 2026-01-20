# Installation Guide for Debian 12 (Bookworm)

This guide covers installing ProFTPD Control Panel on Debian 12 with Python virtual environment.

## Prerequisites

```bash
# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-venv python3-pip git proftpd-basic

# For Apache deployment
apt install -y apache2 libapache2-mod-wsgi-py3

# OR for Nginx deployment
apt install -y nginx
```

## Installation

### 1. Create application directory

```bash
mkdir -p /opt/proftpdcontrol
cd /opt/proftpdcontrol
```

### 2. Download application files

```bash
git clone https://github.com/arheops/proftpdcontrol.git .
```

### 3. Create Python virtual environment

```bash
# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install gunicorn for production
pip install gunicorn
```

### 4. Configure Django

```bash
# Set allowed hosts (replace with your hostname)
HOST_NAME_HERE = `hostname -a` # change if different hostname
sed -i "s/ALLOWED_HOSTS = \[\]/ALLOWED_HOSTS = ['$HOST_NAME_HERE']/" proftpdcontrol/settings.py

# Or for specific host:
# sed -i "s/ALLOWED_HOSTS = \[\]/ALLOWED_HOSTS = ['your-hostname.example.com']/" proftpdcontrol/settings.py

# Generate and set random SECRET_KEY
NEW_SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
sed -i "s/SECRET_KEY = .*/SECRET_KEY = '$NEW_SECRET_KEY'/" proftpdcontrol/settings.py

# Still in venv, run migrations
python manage.py migrate

# Collect static files (for production)
python manage.py collectstatic --noinput

# Create superuser (optional, for Django admin)
python manage.py createsuperuser
```

### 5. Set permissions

```bash
# Set ownership
chown -R www-data:www-data /opt/proftpdcontrol

# Set permissions
chmod -R 755 /opt/proftpdcontrol
chmod 600 /opt/proftpdcontrol/db.sqlite3
```

### 6. Create log directory

```bash
mkdir -p /var/log/proftpdcontrol
chown www-data:www-data /var/log/proftpdcontrol
```

## Deployment Options

### Option A: Systemd + Nginx (Recommended)

#### Install systemd service

```bash
cp contrib/proftpdcontrol.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable proftpdcontrol
systemctl start proftpdcontrol
```

#### Configure Nginx

```bash
cp contrib/nginx-proftpdcontrol.conf /etc/nginx/sites-available/proftpdcontrol

# Edit server_name
nano /etc/nginx/sites-available/proftpdcontrol

# Enable site
ln -s /etc/nginx/sites-available/proftpdcontrol /etc/nginx/sites-enabled/

# Test and reload
nginx -t
systemctl reload nginx
```

### Option B: Systemd + Apache

#### Enable required Apache modules

```bash
a2enmod wsgi proxy proxy_http
```

#### Configure Apache

```bash
cp contrib/apache-proftpdcontrol.conf /etc/apache2/sites-available/proftpdcontrol.conf

# Edit ServerName
nano /etc/apache2/sites-available/proftpdcontrol.conf

# Enable site
a2ensite proftpdcontrol

# Test and reload
apache2ctl configtest
systemctl reload apache2
```

### Option C: Init.d (Legacy)

```bash
cp contrib/proftpdcontrol.init /etc/init.d/proftpdcontrol
chmod +x /etc/init.d/proftpdcontrol
update-rc.d proftpdcontrol defaults
service proftpdcontrol start
```

## ProFTPD Configuration

### 1. Backup existing config

```bash
cp /etc/proftpd/proftpd.conf /etc/proftpd/proftpd.conf.backup
```

### 2. Install base configuration

```bash
cp contrib/proftpd.conf /etc/proftpd/proftpd.conf
```

### 3. Create conf.d directory

```bash
mkdir -p /etc/proftpd/conf.d
```

### 4. Generate and deploy configuration

1. Open the web interface
2. Create users and folders
3. Assign permissions
4. Go to "Generate Config"
5. Download files and copy to server:

```bash
# Copy generated files
cp proftpd.conf /etc/proftpd/conf.d/users.conf
cp ftpd.passwd /etc/proftpd/ftpd.passwd

# Set permissions on password file
chmod 600 /etc/proftpd/ftpd.passwd
chown root:root /etc/proftpd/ftpd.passwd

# Test configuration
proftpd -t

# Restart ProFTPD
systemctl restart proftpd
```

## Production Settings

Edit `/opt/proftpdcontrol/proftpdcontrol/settings.py`:

```python
# Disable debug mode
DEBUG = False

# Set allowed hosts
ALLOWED_HOSTS = ['ftp.example.com', 'your-server-ip']

# Generate new secret key
SECRET_KEY = 'your-new-secret-key-here'

# Static files location
STATIC_ROOT = '/opt/proftpdcontrol/static'
```

Generate a new secret key:

```bash
source /opt/proftpdcontrol/venv/bin/activate
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Firewall Configuration

```bash
# Allow FTP
ufw allow 21/tcp

# Allow passive FTP ports (if configured)
ufw allow 49152:65534/tcp

# Allow HTTP/HTTPS for web interface
ufw allow 80/tcp
ufw allow 443/tcp
```

## Testing

### Test web interface

```bash
curl http://localhost:8000/
```

### Test FTP connection

```bash
ftp localhost
# Enter username and password created in web interface
```

## Troubleshooting

### Check service status

```bash
systemctl status proftpdcontrol
systemctl status proftpd
```

### View logs

```bash
# Application logs
tail -f /var/log/proftpdcontrol/error.log

# ProFTPD logs
tail -f /var/log/proftpd/proftpd.log

# Nginx logs
tail -f /var/log/nginx/proftpdcontrol-error.log
```

### Test ProFTPD configuration

```bash
proftpd -t -c /etc/proftpd/proftpd.conf
```

### Restart services

```bash
systemctl restart proftpdcontrol
systemctl restart proftpd
systemctl restart nginx  # or apache2
```
