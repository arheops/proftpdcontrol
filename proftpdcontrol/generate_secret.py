import string
import secrets
allowed = string.ascii_letters + string.digits + '_-';
print(''.join(secrets.choice(allowed) for _ in range(50))