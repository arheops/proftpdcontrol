import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError

from ftpmanager.models import FTPUser, Folder, FolderAccess, UserProfile


class TestUserProfile:
    """Tests for UserProfile model"""

    def test_profile_auto_created_on_user_creation(self, db):
        """Test that UserProfile is automatically created when User is created"""
        user = User.objects.create_user(username='newuser', password='pass123')
        assert hasattr(user, 'profile')
        assert isinstance(user.profile, UserProfile)

    def test_profile_str_representation(self, user_profile):
        """Test UserProfile string representation"""
        assert str(user_profile) == "Profile for testadmin"

    def test_profile_default_values(self, user_profile):
        """Test UserProfile default values"""
        assert user_profile.basedir == '/main/'
        assert user_profile.exclude_dirs == '/keys/,.ssh'
        assert user_profile.systemuser_regexp == r'.*\..*'

    def test_get_exclude_list_basic(self, user_profile):
        """Test get_exclude_list with default values"""
        exclude_list = user_profile.get_exclude_list()
        assert exclude_list == ['/keys/', '.ssh']

    def test_get_exclude_list_with_spaces(self, user_profile):
        """Test get_exclude_list trims whitespace"""
        user_profile.exclude_dirs = ' /keys/ , .ssh , /tmp/ '
        exclude_list = user_profile.get_exclude_list()
        assert exclude_list == ['/keys/', '.ssh', '/tmp/']

    def test_get_exclude_list_empty(self, user_profile):
        """Test get_exclude_list with empty string"""
        user_profile.exclude_dirs = ''
        exclude_list = user_profile.get_exclude_list()
        assert exclude_list == []

    def test_get_exclude_list_empty_items(self, user_profile):
        """Test get_exclude_list filters out empty items"""
        user_profile.exclude_dirs = '/keys/,,,.ssh,,'
        exclude_list = user_profile.get_exclude_list()
        assert exclude_list == ['/keys/', '.ssh']

    def test_profile_created_on_save_if_not_exists(self, db):
        """Test that profile is created on save if it doesn't exist"""
        user = User.objects.create_user(username='anotheruser', password='pass123')
        # Delete the auto-created profile
        UserProfile.objects.filter(user=user).delete()
        # Reload user and check profile doesn't exist
        user = User.objects.get(pk=user.pk)
        assert not hasattr(user, 'profile') or not UserProfile.objects.filter(user=user).exists()
        # Save user, should create profile
        user.save()
        user.refresh_from_db()
        assert UserProfile.objects.filter(user=user).exists()


class TestFTPUser:
    """Tests for FTPUser model"""

    def test_ftp_user_creation(self, ftp_user):
        """Test FTPUser is created correctly"""
        assert ftp_user.username == 'ftpuser1'
        assert ftp_user.systemuser == '1001'
        assert ftp_user.is_active is True

    def test_ftp_user_str_representation(self, ftp_user):
        """Test FTPUser string representation"""
        assert str(ftp_user) == 'ftpuser1'

    def test_set_password_generates_hash(self, db):
        """Test set_password generates SHA-512 crypt hash"""
        user = FTPUser(username='hashtest', systemuser='1001')
        user.set_password('mypassword')

        # SHA-512 crypt hashes start with $6$
        assert user.password_hash.startswith('$6$')
        assert len(user.password_hash) > 50

    def test_set_password_different_passwords_different_hashes(self, db):
        """Test that different passwords produce different hashes"""
        user1 = FTPUser(username='user1', systemuser='1001')
        user1.set_password('password1')

        user2 = FTPUser(username='user2', systemuser='1001')
        user2.set_password('password2')

        assert user1.password_hash != user2.password_hash

    def test_set_password_same_password_different_hashes(self, db):
        """Test that same password produces different hashes (due to salt)"""
        user1 = FTPUser(username='user1', systemuser='1001')
        user1.set_password('samepass')

        user2 = FTPUser(username='user2', systemuser='1001')
        user2.set_password('samepass')

        # Hashes should differ due to different salts
        assert user1.password_hash != user2.password_hash

    def test_ftp_user_unique_username(self, db, ftp_user):
        """Test that FTPUser username must be unique"""
        with pytest.raises(IntegrityError):
            FTPUser.objects.create(username='ftpuser1', systemuser='1002')

    def test_ftp_user_default_is_active(self, db):
        """Test that FTPUser is active by default"""
        user = FTPUser.objects.create(username='defaultactive', systemuser='1001')
        assert user.is_active is True

    def test_ftp_user_timestamps(self, db):
        """Test that timestamps are set correctly"""
        user = FTPUser.objects.create(username='timestamptest', systemuser='1001')
        assert user.created_at is not None
        assert user.updated_at is not None


class TestFolder:
    """Tests for Folder model"""

    def test_folder_creation(self, folder):
        """Test Folder is created correctly"""
        assert folder.name == 'Test Folder'
        assert folder.path == '/data/test'
        assert folder.description == 'A test folder'

    def test_folder_str_representation(self, folder):
        """Test Folder string representation"""
        assert str(folder) == 'Test Folder (/data/test)'

    def test_folder_unique_path(self, db, folder):
        """Test that folder path must be unique"""
        with pytest.raises(IntegrityError):
            Folder.objects.create(name='Duplicate', path='/data/test')

    def test_folder_ordering(self, db):
        """Test folders are ordered by name"""
        Folder.objects.create(name='Zebra', path='/zebra')
        Folder.objects.create(name='Alpha', path='/alpha')
        Folder.objects.create(name='Middle', path='/middle')

        folders = list(Folder.objects.all())
        names = [f.name for f in folders]
        assert names == sorted(names)


class TestFolderAccess:
    """Tests for FolderAccess model"""

    def test_folder_access_creation(self, folder_access_read):
        """Test FolderAccess is created correctly"""
        assert folder_access_read.permission == 'read'

    def test_folder_access_str_representation(self, folder_access_read):
        """Test FolderAccess string representation"""
        assert str(folder_access_read) == 'ftpuser1 -> Test Folder (read)'

    def test_folder_access_write_permission(self, folder_access_write):
        """Test FolderAccess with write permission"""
        assert folder_access_write.permission == 'write'
        assert str(folder_access_write) == 'ftpuser1 -> Second Folder (write)'

    def test_folder_access_unique_together(self, db, ftp_user, folder, folder_access_read):
        """Test that user-folder combination must be unique"""
        with pytest.raises(IntegrityError):
            FolderAccess.objects.create(user=ftp_user, folder=folder, permission='write')

    def test_folder_access_permission_choices(self, db, ftp_user, folder):
        """Test that permission choices are limited"""
        # Valid permissions
        FolderAccess.objects.filter(user=ftp_user, folder=folder).delete()

        access = FolderAccess.objects.create(user=ftp_user, folder=folder, permission='read')
        assert access.permission == 'read'

        access.permission = 'write'
        access.save()
        assert access.permission == 'write'

    def test_folder_access_cascade_delete_user(self, db, ftp_user, folder, folder_access_read):
        """Test that FolderAccess is deleted when FTPUser is deleted"""
        access_id = folder_access_read.id
        ftp_user.delete()
        assert not FolderAccess.objects.filter(id=access_id).exists()

    def test_folder_access_cascade_delete_folder(self, db, ftp_user, folder, folder_access_read):
        """Test that FolderAccess is deleted when Folder is deleted"""
        access_id = folder_access_read.id
        folder.delete()
        assert not FolderAccess.objects.filter(id=access_id).exists()
