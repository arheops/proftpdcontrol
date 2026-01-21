import pytest

from ftpmanager.models import FTPUser, Folder, FolderAccess, UserProfile
from ftpmanager.forms import (
    FTPUserForm,
    FolderForm,
    FolderAccessForm,
    BulkAccessForm,
    UserProfileForm,
)


class TestFTPUserForm:
    """Tests for FTPUserForm"""

    def test_form_valid_with_password(self, db):
        """Test form is valid with all required fields"""
        form = FTPUserForm(data={
            'username': 'newuser',
            'systemuser': '1001',
            'is_active': True,
            'password': 'secretpass',
        })
        assert form.is_valid()

    def test_form_valid_without_password(self, db):
        """Test form is valid without password (for updates)"""
        form = FTPUserForm(data={
            'username': 'newuser',
            'systemuser': '1001',
            'is_active': True,
        })
        assert form.is_valid()

    def test_form_save_with_password(self, db):
        """Test that save sets password when provided"""
        form = FTPUserForm(data={
            'username': 'newuser',
            'systemuser': '1001',
            'is_active': True,
            'password': 'secretpass',
        })
        assert form.is_valid()
        user = form.save()

        assert user.username == 'newuser'
        assert user.password_hash.startswith('$6$')

    def test_form_save_without_password(self, db):
        """Test that save doesn't modify password when not provided"""
        form = FTPUserForm(data={
            'username': 'newuser',
            'systemuser': '1001',
            'is_active': True,
        })
        assert form.is_valid()
        user = form.save()

        assert user.username == 'newuser'
        assert user.password_hash == ''

    def test_form_update_with_password(self, db, ftp_user):
        """Test that update changes password when provided"""
        old_hash = ftp_user.password_hash

        form = FTPUserForm(data={
            'username': ftp_user.username,
            'systemuser': '1001',
            'is_active': True,
            'password': 'newpassword',
        }, instance=ftp_user)

        assert form.is_valid()
        user = form.save()

        assert user.password_hash != old_hash

    def test_form_update_without_password_keeps_old(self, db, ftp_user):
        """Test that update keeps old password when not provided"""
        old_hash = ftp_user.password_hash

        form = FTPUserForm(data={
            'username': ftp_user.username,
            'systemuser': '1001',
            'is_active': True,
        }, instance=ftp_user)

        assert form.is_valid()
        user = form.save()

        assert user.password_hash == old_hash

    def test_form_invalid_missing_username(self, db):
        """Test form is invalid without username"""
        form = FTPUserForm(data={
            'systemuser': '1001',
            'is_active': True,
        })
        assert not form.is_valid()
        assert 'username' in form.errors

    def test_form_widgets(self, db):
        """Test that form widgets have correct classes"""
        form = FTPUserForm()
        assert 'form-control' in form.fields['username'].widget.attrs.get('class', '')
        assert 'form-control' in form.fields['systemuser'].widget.attrs.get('class', '')


class TestFolderForm:
    """Tests for FolderForm"""

    def test_form_valid(self, db):
        """Test form is valid with required fields"""
        form = FolderForm(data={
            'name': 'Test Folder',
            'path': '/data/test',
            'description': 'A test folder',
        })
        assert form.is_valid()

    def test_form_valid_without_description(self, db):
        """Test form is valid without optional description"""
        form = FolderForm(data={
            'name': 'Test Folder',
            'path': '/data/test',
        })
        assert form.is_valid()

    def test_form_save(self, db):
        """Test form save creates folder"""
        form = FolderForm(data={
            'name': 'New Folder',
            'path': '/data/new',
            'description': 'Description',
        })
        assert form.is_valid()
        folder = form.save()

        assert folder.name == 'New Folder'
        assert folder.path == '/data/new'

    def test_form_invalid_missing_name(self, db):
        """Test form is invalid without name"""
        form = FolderForm(data={
            'path': '/data/test',
        })
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_form_invalid_missing_path(self, db):
        """Test form is invalid without path"""
        form = FolderForm(data={
            'name': 'Test Folder',
        })
        assert not form.is_valid()
        assert 'path' in form.errors

    def test_form_widgets(self, db):
        """Test that form widgets have correct classes"""
        form = FolderForm()
        assert 'form-control' in form.fields['name'].widget.attrs.get('class', '')
        assert 'form-control' in form.fields['path'].widget.attrs.get('class', '')


class TestFolderAccessForm:
    """Tests for FolderAccessForm"""

    def test_form_valid(self, db, ftp_user, folder):
        """Test form is valid with all fields"""
        form = FolderAccessForm(data={
            'user': ftp_user.pk,
            'folder': folder.pk,
            'permission': 'read',
        })
        assert form.is_valid()

    def test_form_save(self, db, ftp_user, folder):
        """Test form save creates folder access"""
        form = FolderAccessForm(data={
            'user': ftp_user.pk,
            'folder': folder.pk,
            'permission': 'write',
        })
        assert form.is_valid()
        access = form.save()

        assert access.user == ftp_user
        assert access.folder == folder
        assert access.permission == 'write'

    def test_form_widgets(self, db):
        """Test that form widgets have correct classes"""
        form = FolderAccessForm()
        assert 'form-select' in form.fields['user'].widget.attrs.get('class', '')
        assert 'form-select' in form.fields['folder'].widget.attrs.get('class', '')
        assert 'form-select' in form.fields['permission'].widget.attrs.get('class', '')


class TestBulkAccessForm:
    """Tests for BulkAccessForm"""

    def test_form_creates_folder_fields(self, db, folder, folder2):
        """Test that form creates fields for each folder"""
        form = BulkAccessForm()

        assert f'folder_{folder.pk}' in form.fields
        assert f'folder_{folder2.pk}' in form.fields

    def test_form_folder_field_choices(self, db, folder):
        """Test that folder fields have correct choices"""
        form = BulkAccessForm()
        field = form.fields[f'folder_{folder.pk}']

        assert ('none', 'No Access') in field.choices
        assert ('read', 'Read Only') in field.choices
        assert ('write', 'Read & Write') in field.choices

    def test_form_folder_field_label(self, db, folder):
        """Test that folder fields have folder name as label"""
        form = BulkAccessForm()
        field = form.fields[f'folder_{folder.pk}']

        assert field.label == folder.name

    def test_form_valid_with_user(self, db, ftp_user, folder):
        """Test form is valid with user and folder selection"""
        form = BulkAccessForm(data={
            'user': ftp_user.pk,
            f'folder_{folder.pk}': 'read',
        })
        assert form.is_valid()

    def test_form_no_folders(self, db, ftp_user):
        """Test form with no folders in database"""
        form = BulkAccessForm()
        # Should only have the 'user' field
        folder_fields = [f for f in form.fields.keys() if f.startswith('folder_')]
        assert len(folder_fields) == 0


class TestUserProfileForm:
    """Tests for UserProfileForm"""

    def test_form_valid(self, db, user_profile):
        """Test form is valid with all fields"""
        form = UserProfileForm(data={
            'basedir': '/data/',
            'exclude_dirs': '/private/,.hidden',
        }, instance=user_profile)
        assert form.is_valid()

    def test_form_save(self, db, user_profile):
        """Test form save updates profile"""
        form = UserProfileForm(data={
            'basedir': '/newbase/',
            'exclude_dirs': '/secret/',
        }, instance=user_profile)
        assert form.is_valid()
        profile = form.save()

        assert profile.basedir == '/newbase/'
        assert profile.exclude_dirs == '/secret/'

    def test_form_fields(self, db):
        """Test form has correct fields"""
        form = UserProfileForm()
        assert 'basedir' in form.fields
        assert 'exclude_dirs' in form.fields
        # systemuser_regexp should not be editable from form
        assert 'systemuser_regexp' not in form.fields

    def test_form_widgets(self, db):
        """Test that form widgets have correct classes"""
        form = UserProfileForm()
        assert 'form-control' in form.fields['basedir'].widget.attrs.get('class', '')
        assert 'form-control' in form.fields['exclude_dirs'].widget.attrs.get('class', '')
