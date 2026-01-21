import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

from django.urls import reverse

from ftpmanager.models import FTPUser, Folder, FolderAccess, UserProfile


class TestDashboardView:
    """Tests for dashboard view"""

    def test_dashboard_requires_login(self, client, db):
        """Test that dashboard requires authentication"""
        response = client.get(reverse('dashboard'))
        assert response.status_code == 302
        assert 'login' in response.url

    def test_dashboard_authenticated(self, authenticated_client):
        """Test dashboard is accessible when authenticated"""
        response = authenticated_client.get(reverse('dashboard'))
        assert response.status_code == 200

    def test_dashboard_context(self, authenticated_client, ftp_user, folder, folder_access_read):
        """Test dashboard context contains correct data"""
        response = authenticated_client.get(reverse('dashboard'))

        assert 'users_count' in response.context
        assert 'folders_count' in response.context
        assert 'access_rules_count' in response.context
        assert response.context['users_count'] == 1
        assert response.context['folders_count'] == 1
        assert response.context['access_rules_count'] == 1


class TestUserListView:
    """Tests for user list view"""

    def test_user_list_requires_login(self, client, db):
        """Test that user list requires authentication"""
        response = client.get(reverse('user_list'))
        assert response.status_code == 302

    def test_user_list_authenticated(self, authenticated_client):
        """Test user list is accessible when authenticated"""
        response = authenticated_client.get(reverse('user_list'))
        assert response.status_code == 200

    def test_user_list_shows_users(self, authenticated_client, ftp_user):
        """Test user list shows users"""
        response = authenticated_client.get(reverse('user_list'))
        assert 'users' in response.context
        assert ftp_user in response.context['users']


class TestUserCreateView:
    """Tests for user create view"""

    def test_user_create_requires_login(self, client, db):
        """Test that user create requires authentication"""
        response = client.get(reverse('user_create'))
        assert response.status_code == 302

    def test_user_create_get(self, authenticated_client):
        """Test user create form is displayed"""
        response = authenticated_client.get(reverse('user_create'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_user_create_post_success(self, authenticated_client, db):
        """Test successful user creation"""
        response = authenticated_client.post(reverse('user_create'), {
            'username': 'newftpuser',
            'systemuser': '1001',
            'is_active': True,
            'password': 'secret123',
        })

        assert response.status_code == 302
        assert FTPUser.objects.filter(username='newftpuser').exists()

    def test_user_create_post_invalid(self, authenticated_client, db):
        """Test user creation with invalid data"""
        response = authenticated_client.post(reverse('user_create'), {
            'systemuser': '1001',
            # missing username
        })

        assert response.status_code == 200
        assert not FTPUser.objects.filter(systemuser='1001').exists()


class TestUserEditView:
    """Tests for user edit view"""

    def test_user_edit_requires_login(self, client, db, ftp_user):
        """Test that user edit requires authentication"""
        response = client.get(reverse('user_edit', args=[ftp_user.pk]))
        assert response.status_code == 302

    def test_user_edit_get(self, authenticated_client, ftp_user):
        """Test user edit form is displayed"""
        response = authenticated_client.get(reverse('user_edit', args=[ftp_user.pk]))
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].instance == ftp_user

    def test_user_edit_post_success(self, authenticated_client, ftp_user):
        """Test successful user edit"""
        response = authenticated_client.post(reverse('user_edit', args=[ftp_user.pk]), {
            'username': 'updateduser',
            'systemuser': '1002',
            'is_active': True,
        })

        assert response.status_code == 302
        ftp_user.refresh_from_db()
        assert ftp_user.username == 'updateduser'

    def test_user_edit_not_found(self, authenticated_client, db):
        """Test user edit with non-existent user"""
        response = authenticated_client.get(reverse('user_edit', args=[9999]))
        assert response.status_code == 404


class TestUserDeleteView:
    """Tests for user delete view"""

    def test_user_delete_requires_login(self, client, db, ftp_user):
        """Test that user delete requires authentication"""
        response = client.post(reverse('user_delete', args=[ftp_user.pk]))
        assert response.status_code == 302

    def test_user_delete_get(self, authenticated_client, ftp_user):
        """Test user delete confirmation page"""
        response = authenticated_client.get(reverse('user_delete', args=[ftp_user.pk]))
        assert response.status_code == 200

    def test_user_delete_post_success(self, authenticated_client, ftp_user):
        """Test successful user deletion"""
        pk = ftp_user.pk
        response = authenticated_client.post(reverse('user_delete', args=[pk]))

        assert response.status_code == 302
        assert not FTPUser.objects.filter(pk=pk).exists()


class TestUserAccessView:
    """Tests for user access management view"""

    def test_user_access_requires_login(self, client, db, ftp_user):
        """Test that user access requires authentication"""
        response = client.get(reverse('user_access', args=[ftp_user.pk]))
        assert response.status_code == 302

    def test_user_access_get(self, authenticated_client, ftp_user, folder):
        """Test user access page is displayed"""
        response = authenticated_client.get(reverse('user_access', args=[ftp_user.pk]))
        assert response.status_code == 200
        assert 'user' in response.context
        assert 'folders' in response.context
        assert 'current_access' in response.context

    def test_user_access_post_add_access(self, authenticated_client, ftp_user, folder):
        """Test adding folder access"""
        response = authenticated_client.post(reverse('user_access', args=[ftp_user.pk]), {
            f'folder_{folder.pk}': 'read',
        })

        assert response.status_code == 302
        assert FolderAccess.objects.filter(user=ftp_user, folder=folder, permission='read').exists()

    def test_user_access_post_update_access(self, authenticated_client, ftp_user, folder, folder_access_read):
        """Test updating folder access"""
        response = authenticated_client.post(reverse('user_access', args=[ftp_user.pk]), {
            f'folder_{folder.pk}': 'write',
        })

        assert response.status_code == 302
        access = FolderAccess.objects.get(user=ftp_user, folder=folder)
        assert access.permission == 'write'

    def test_user_access_post_remove_access(self, authenticated_client, ftp_user, folder, folder_access_read):
        """Test removing folder access"""
        response = authenticated_client.post(reverse('user_access', args=[ftp_user.pk]), {
            f'folder_{folder.pk}': 'none',
        })

        assert response.status_code == 302
        assert not FolderAccess.objects.filter(user=ftp_user, folder=folder).exists()


class TestFolderListView:
    """Tests for folder list view"""

    def test_folder_list_requires_login(self, client, db):
        """Test that folder list requires authentication"""
        response = client.get(reverse('folder_list'))
        assert response.status_code == 302

    def test_folder_list_authenticated(self, authenticated_client, folder):
        """Test folder list shows folders"""
        response = authenticated_client.get(reverse('folder_list'))
        assert response.status_code == 200
        assert 'folders' in response.context


class TestFolderCreateView:
    """Tests for folder create view"""

    def test_folder_create_get(self, authenticated_client):
        """Test folder create form is displayed"""
        response = authenticated_client.get(reverse('folder_create'))
        assert response.status_code == 200

    def test_folder_create_post_success(self, authenticated_client, db):
        """Test successful folder creation"""
        response = authenticated_client.post(reverse('folder_create'), {
            'name': 'New Folder',
            'path': '/data/newfolder',
            'description': 'A new folder',
        })

        assert response.status_code == 302
        assert Folder.objects.filter(path='/data/newfolder').exists()


class TestFolderEditView:
    """Tests for folder edit view"""

    def test_folder_edit_get(self, authenticated_client, folder):
        """Test folder edit form is displayed"""
        response = authenticated_client.get(reverse('folder_edit', args=[folder.pk]))
        assert response.status_code == 200

    def test_folder_edit_post_success(self, authenticated_client, folder):
        """Test successful folder edit"""
        response = authenticated_client.post(reverse('folder_edit', args=[folder.pk]), {
            'name': 'Updated Folder',
            'path': folder.path,
            'description': 'Updated description',
        })

        assert response.status_code == 302
        folder.refresh_from_db()
        assert folder.name == 'Updated Folder'


class TestFolderDeleteView:
    """Tests for folder delete view"""

    def test_folder_delete_get(self, authenticated_client, folder):
        """Test folder delete confirmation page"""
        response = authenticated_client.get(reverse('folder_delete', args=[folder.pk]))
        assert response.status_code == 200

    def test_folder_delete_post_success(self, authenticated_client, folder):
        """Test successful folder deletion"""
        pk = folder.pk
        response = authenticated_client.post(reverse('folder_delete', args=[pk]))

        assert response.status_code == 302
        assert not Folder.objects.filter(pk=pk).exists()


class TestGenerateConfigView:
    """Tests for config generation view"""

    def test_generate_config_requires_login(self, client, db):
        """Test that generate config requires authentication"""
        response = client.get(reverse('generate_config'))
        assert response.status_code == 302

    def test_generate_config_page(self, authenticated_client):
        """Test generate config page is displayed"""
        response = authenticated_client.get(reverse('generate_config'))
        assert response.status_code == 200
        assert 'config' in response.context
        assert 'ftpusers' in response.context


class TestDownloadConfigView:
    """Tests for config download view"""

    def test_download_config_requires_login(self, client, db):
        """Test that download config requires authentication"""
        response = client.get(reverse('download_config'))
        assert response.status_code == 302

    def test_download_config(self, authenticated_client):
        """Test config file download"""
        response = authenticated_client.get(reverse('download_config'))

        assert response.status_code == 200
        assert response['Content-Type'] == 'text/plain'
        assert 'attachment; filename="proftpd.conf"' in response['Content-Disposition']


class TestDownloadFtpusersView:
    """Tests for ftpusers file download view"""

    def test_download_ftpusers_requires_login(self, client, db):
        """Test that download ftpusers requires authentication"""
        response = client.get(reverse('download_ftpusers'))
        assert response.status_code == 302

    def test_download_ftpusers(self, authenticated_client):
        """Test ftpusers file download"""
        response = authenticated_client.get(reverse('download_ftpusers'))

        assert response.status_code == 200
        assert response['Content-Type'] == 'text/plain'
        assert 'attachment; filename="ftpd.passwd"' in response['Content-Disposition']


class TestProfileSettingsView:
    """Tests for profile settings view"""

    def test_profile_settings_requires_login(self, client, db):
        """Test that profile settings requires authentication"""
        response = client.get(reverse('profile_settings'))
        assert response.status_code == 302

    def test_profile_settings_get(self, authenticated_client):
        """Test profile settings page is displayed"""
        response = authenticated_client.get(reverse('profile_settings'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_profile_settings_post_success(self, authenticated_client, django_user):
        """Test successful profile settings update"""
        response = authenticated_client.post(reverse('profile_settings'), {
            'basedir': '/newbase/',
            'exclude_dirs': '/secret/',
        })

        assert response.status_code == 302
        django_user.profile.refresh_from_db()
        assert django_user.profile.basedir == '/newbase/'


class TestListDirectoriesView:
    """Tests for list directories API view"""

    def test_list_directories_requires_login(self, client, db):
        """Test that list directories requires authentication"""
        response = client.get(reverse('list_directories'))
        assert response.status_code == 302

    def test_list_directories_basedir_not_found(self, authenticated_client, django_user):
        """Test response when basedir doesn't exist"""
        django_user.profile.basedir = '/nonexistent/path/'
        django_user.profile.save()

        response = authenticated_client.get(reverse('list_directories'))

        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'error' in data
        assert 'directories' in data
        assert data['directories'] == []

    def test_list_directories_success(self, authenticated_client, django_user):
        """Test successful directory listing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create subdirectories
            os.makedirs(os.path.join(tmpdir, 'subdir1'))
            os.makedirs(os.path.join(tmpdir, 'subdir2'))

            django_user.profile.basedir = tmpdir
            django_user.profile.exclude_dirs = ''
            django_user.profile.save()

            response = authenticated_client.get(reverse('list_directories'))

            assert response.status_code == 200
            data = json.loads(response.content)
            assert 'directories' in data
            # Check that subdirectories are found (handle both path separators)
            dirs = data['directories']
            assert any('subdir1' in d for d in dirs)
            assert any('subdir2' in d for d in dirs)

    def test_list_directories_excludes(self, authenticated_client, django_user):
        """Test that excluded directories are filtered"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create subdirectories
            os.makedirs(os.path.join(tmpdir, 'visible'))
            os.makedirs(os.path.join(tmpdir, 'hidden'))

            django_user.profile.basedir = tmpdir
            django_user.profile.exclude_dirs = 'hidden'
            django_user.profile.save()

            response = authenticated_client.get(reverse('list_directories'))

            assert response.status_code == 200
            data = json.loads(response.content)
            dirs = data['directories']
            assert any('visible' in d for d in dirs)
            assert not any('hidden' in d for d in dirs)


class TestListSystemusersView:
    """Tests for list systemusers API view"""

    def test_list_systemusers_requires_login(self, client, db):
        """Test that list systemusers requires authentication"""
        response = client.get(reverse('list_systemusers'))
        assert response.status_code == 302

    @patch('ftpmanager.views.os.path.isfile')
    def test_list_systemusers_passwd_not_found(self, mock_isfile, authenticated_client):
        """Test response when /etc/passwd doesn't exist"""
        mock_isfile.return_value = False

        response = authenticated_client.get(reverse('list_systemusers'))

        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'error' in data
        assert 'users' in data
        assert data['users'] == []

    def test_list_systemusers_invalid_regex(self, authenticated_client, django_user):
        """Test response with invalid regex pattern"""
        django_user.profile.systemuser_regexp = '[invalid'
        django_user.profile.save()

        with patch('ftpmanager.views.os.path.isfile', return_value=True):
            response = authenticated_client.get(reverse('list_systemusers'))

        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'error' in data
        assert 'Invalid regexp' in data['error']

    @patch('builtins.open')
    @patch('ftpmanager.views.os.path.isfile')
    def test_list_systemusers_success(self, mock_isfile, mock_open, authenticated_client, django_user):
        """Test successful system user listing"""
        mock_isfile.return_value = True
        mock_open.return_value.__enter__.return_value = iter([
            'user.name:x:1000:1000::/home/user.name:/bin/bash\n',
            'another.user:x:1001:1001::/home/another.user:/bin/bash\n',
            'regularuser:x:1002:1002::/home/regularuser:/bin/bash\n',
        ])

        django_user.profile.systemuser_regexp = r'.*\..*'  # Match users with a dot
        django_user.profile.save()

        response = authenticated_client.get(reverse('list_systemusers'))

        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'users' in data
        assert 'user.name' in data['users']
        assert 'another.user' in data['users']
        assert 'regularuser' not in data['users']

    @patch('builtins.open')
    @patch('ftpmanager.views.os.path.isfile')
    def test_list_systemusers_permission_denied(self, mock_isfile, mock_open, authenticated_client):
        """Test response when permission denied reading /etc/passwd"""
        mock_isfile.return_value = True
        mock_open.side_effect = PermissionError('Permission denied')

        response = authenticated_client.get(reverse('list_systemusers'))

        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'error' in data
        assert 'Permission denied' in data['error']
