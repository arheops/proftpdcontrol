from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from passlib.hash import sha512_crypt


class UserProfile(models.Model):
    """Extended profile for Django users with directory settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    basedir = models.CharField(max_length=500, default='/main/', help_text='Base directory for folder lookup')
    exclude_dirs = models.CharField(max_length=500, default='/keys/,.ssh', help_text='Comma-separated list of directories to exclude')

    def __str__(self):
        return f"Profile for {self.user.username}"

    def get_exclude_list(self):
        """Return exclude_dirs as a list"""
        return [d.strip() for d in self.exclude_dirs.split(',') if d.strip()]


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create profile when user is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Auto-save profile when user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)


class FTPUser(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password_hash = models.CharField(max_length=255, blank=True)
    systemuser = models.CharField(max_length=100, default='1001', help_text='System username or UID for file ownership')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, raw_password):
        """Generate SHA-512 crypt hash for ProFTPD compatibility"""
        self.password_hash = sha512_crypt.hash(raw_password)

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
