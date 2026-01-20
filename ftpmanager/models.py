from django.db import models
import crypt
import secrets
import string


class FTPUser(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password_hash = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, raw_password):
        """Generate SHA-512 crypt hash for ProFTPD compatibility"""
        # Generate random salt for SHA-512 crypt
        salt_chars = string.ascii_letters + string.digits + './'
        salt = ''.join(secrets.choice(salt_chars) for _ in range(16))
        # Use SHA-512 crypt ($6$)
        self.password_hash = crypt.crypt(raw_password, f'$6${salt}$')

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "FTP User"
        verbose_name_plural = "FTP Users"


class Folder(models.Model):
    name = models.CharField(max_length=200)
    path = models.CharField(max_length=500, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.path})"

    class Meta:
        ordering = ['name']


class FolderAccess(models.Model):
    PERMISSION_CHOICES = [
        ('read', 'Read Only'),
        ('write', 'Read & Write'),
    ]

    user = models.ForeignKey(FTPUser, on_delete=models.CASCADE, related_name='folder_access')
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='user_access')
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default='read')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} -> {self.folder.name} ({self.permission})"

    class Meta:
        verbose_name = "Folder Access"
        verbose_name_plural = "Folder Access"
        unique_together = ['user', 'folder']
