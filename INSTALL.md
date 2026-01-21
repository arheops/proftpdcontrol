# Installation Guide for Debian 12 (Bookworm)

This guide covers installing ProFTPD Control Panel on Debian 12 with Python virtual environment and HTTPS.

## Prerequisites

```bash
# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-venv python3-pip git proftpd-basic

# For Nginx deployment (recommended)
apt install -y nginx certbot python3-certbot-nginx

# OR for Apache deployment
apt install -y apache2 libapache2-mod-wsgi-py3 certbot python3-certbot-apache
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
export EMAIL_HERE="root@localhost" # change email to your admin email
export HOST_NAME_HERE="`hostname`" # change if different hostname
sed -i "s/ALLOWED_HOSTS = \[.*\]/ALLOWED_HOSTS = ['$HOST_NAME_HERE']/" proftpdcontrol/settings.py

# Or for specific host:
# sed -i "s/ALLOWED_HOSTS = \[\]/ALLOWED_HOSTS = ['your-hostname.example.com']/" proftpdcontrol/settings.py

# Generate and set random SECRET_KEY
NEW_SECRET_KEY=$(python proftpdcontrol/generate_secret.py)
sed -i "s/^SECRET_KEY =.*\$/SECRET_KEY = '$NEW_SECRET_KEY'/" proftpdcontrol/settings.py

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

## Deployment with Nginx + HTTPS (Recommended)

### 1. Install systemd service

```bash
cp contrib/proftpdcontrol.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable proftpdcontrol
systemctl start proftpdcontrol
```

### 2. Configure Nginx (initial HTTP setup for Let's Encrypt)

```bash
# Create temporary HTTP-only config for certificate issuance
cat > /etc/nginx/sites-available/proftpdcontrol << 'EOF'
server {
    listen 80;
    server_name ftp.example.com;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/proftpdcontrol/static;
    }
}
EOF
# change server name
sed -e "s/ftp.example.com/$HOST_NAME_HERE/g" /etc/nginx/sites-available/proftpdcontrol

# Edit server_name to match your domain
#nano /etc/nginx/sites-available/proftpdcontrol

# Enable site and remove default
ln -sf /etc/nginx/sites-available/proftpdcontrol /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload
nginx -t
systemctl reload nginx
```

### 3. Obtain Let's Encrypt certificate

```bash
# Replace ftp.example.com with your domain
apt-get install certbot python3-certbot-nginx
certbot --nginx -d $HOST_NAME_HERE -m $EMAIL_HERE --agree-tos --no-eff-email

# Follow the prompts:
# - Enter email for renewal notices
# - Agree to terms of service
# - Choose whether to redirect HTTP to HTTPS (recommended: yes)
```

### 4. Install full HTTPS configuration

```bash
# Copy the production config
cp contrib/nginx-proftpdcontrol.conf /etc/nginx/sites-available/proftpdcontrol

# Edit server_name and certificate paths to match your domain
sed -i "s/ftp.example.com/$HOST_NAME_HERE/g" /etc/nginx/sites-available/proftpdcontrol

# Test and reload
nginx -t
systemctl reload nginx
```

### 5. Verify automatic certificate renewal

```bash
# Test renewal (dry run)
certbot renew --pre-hook "service nginx stop" --post-hook "service nginx start" --standalone
sed -i 's|ExecStart=.*|ExecStart=/usr/bin/certbot -q renew --no-random-sleep-on-renew --pre-hook "service nginx stop" --post-hook "service nginx start" --standalone|' \
  /lib/systemd/system/certbot.service

# Certbot automatically installs a systemd timer for renewal
systemctl status certbot.timer
```

## Alternative: Apache + HTTPS

### 1. Enable required Apache modules

```bash
a2enmod wsgi proxy proxy_http ssl headers
```

### 2. Configure Apache (initial setup)

```bash
cp contrib/apache-proftpdcontrol.conf /etc/apache2/sites-available/proftpdcontrol.conf

# Edit ServerName
nano /etc/apache2/sites-available/proftpdcontrol.conf

# Enable site
a2ensite proftpdcontrol
a2dissite 000-default

# Test and reload
apache2ctl configtest
systemctl reload apache2
```

### 3. Obtain Let's Encrypt certificate

```bash
# Replace ftp.example.com with your domain
certbot --apache -d ftp.example.com
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

1. Open the web interface (https://your-domain/)
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

# HTTPS settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
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

# Allow HTTPS for web interface
ufw allow 443/tcp

# Allow HTTP for Let's Encrypt renewal
ufw allow 80/tcp
```

## Testing

### Test web interface

```bash
curl -I https://your-domain/
```

### Test SSL certificate

```bash
openssl s_client -connect your-domain:443 -servername your-domain
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
systemctl status nginx
```

### View logs

```bash
# Application logs
tail -f /var/log/proftpdcontrol/error.log

# ProFTPD logs
tail -f /var/log/proftpd/proftpd.log

# Nginx logs
tail -f /var/log/nginx/proftpdcontrol-error.log

# Let's Encrypt logs
tail -f /var/log/letsencrypt/letsencrypt.log
```

### Certificate issues

```bash
# Check certificate status
certbot certificates

# Force renewal
certbot renew --force-renewal

# Check certificate expiry
echo | openssl s_client -connect your-domain:443 2>/dev/null | openssl x509 -noout -dates
```

### Test ProFTPD configuration

```bash
proftpd -t -c /etc/proftpd/proftpd.conf
```

### Restart services

```bash
systemctl restart proftpdcontrol
systemctl restart proftpd
systemctl restart nginx
```

## Automatic Config Deployment (Cron)

Set up automatic deployment of ProFTPD configuration changes:

### 1. Copy and set permissions on deploy script

```bash
cp /opt/proftpdcontrol/contrib/proftp_restart.sh /usr/local/bin/
chmod +x /usr/local/bin/proftp_restart.sh
```

### 2. Add to crontab

```bash
# Edit root crontab
crontab -e

# Add line to run every 5 minutes:
*/5 * * * * /usr/local/bin/proftp_restart.sh >> /var/log/proftpdcontrol/cron.log 2>&1
```

The script only restarts ProFTPD if configuration files have changed.
