import pytest
from django.contrib.auth.models import User

from ftpmanager.models import FTPUser, Folder, FolderAccess, UserProfile


@pytest.fixture
def django_user(db):
    """Create a Django user for testing"""
    user = User.objects.create_user(
        username='testadmin',
        email='admin@test.com',
        password='testpass123'
    )
    return user


@pytest.fixture
def user_profile(db, django_user):
    """Get the auto-created user profile"""
    return django_user.profile


@pytest.fixture
def ftp_user(db):
    """Create an FTP user for testing"""
    user = FTPUser.objects.create(
        username='ftpuser1',
        systemuser='1001',
        is_active=True
    )
    user.set_password('secret123')
    user.save()
    return user


@pytest.fixture
def inactive_ftp_user(db):
    """Create an inactive FTP user for testing"""
    user = FTPUser.objects.create(
        username='inactiveuser',
        systemuser='1002',
        is_active=False
    )
    user.set_password('secret456')
    user.save()
    return user


@pytest.fixture
def folder(db):
    """Create a folder for testing"""
    return Folder.objects.create(
        name='Test Folder',
        path='/data/test',
        description='A test folder'
    )


@pytest.fixture
def folder2(db):
    """Create a second folder for testing"""
    return Folder.objects.create(
        name='Second Folder',
        path='/data/second',
        description='Another test folder'
    )


@pytest.fixture
def folder_access_read(db, ftp_user, folder):
    """Create read-only folder access"""
    return FolderAccess.objects.create(
        user=ftp_user,
        folder=folder,
        permission='read'
    )


@pytest.fixture
def folder_access_write(db, ftp_user, folder2):
    """Create read-write folder access"""
    return FolderAccess.objects.create(
        user=ftp_user,
        folder=folder2,
        permission='write'
    )


@pytest.fixture
def authenticated_client(client, django_user):
    """Return a client logged in as the test user"""
    client.login(username='testadmin', password='testpass123')
    return client
