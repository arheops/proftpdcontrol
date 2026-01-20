#!/bin/bash
# ProFTPD Config Deployment Script
# Run via cron to automatically deploy configuration changes

cd /opt/proftpdcontrol
source venv/bin/activate
python manage.py deploy_config --config-dir /etc/proftpd --passwd-file ftpd.passwd --restart
