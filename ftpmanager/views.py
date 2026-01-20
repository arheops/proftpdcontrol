import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .models import FTPUser, Folder, FolderAccess, UserProfile
from .forms import FTPUserForm, FolderForm, FolderAccessForm, UserProfileForm
from .config_generator import generate_proftpd_config, generate_ftpusers_file


@login_required
def dashboard(request):
    """Main dashboard showing overview"""
    context = {
        'users_count': FTPUser.objects.filter(is_active=True).count(),
        'folders_count': Folder.objects.count(),
        'access_rules_count': FolderAccess.objects.count(),
        'recent_users': FTPUser.objects.order_by('-created_at')[:5],
        'recent_access': FolderAccess.objects.select_related('user', 'folder').order_by('-created_at')[:10],
    }
    return render(request, 'ftpmanager/dashboard.html', context)


# FTP User Views
@login_required
def user_list(request):
    users = FTPUser.objects.prefetch_related('folder_access__folder').all()
    return render(request, 'ftpmanager/user_list.html', {'users': users})


@login_required
def user_create(request):
    if request.method == 'POST':
        form = FTPUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = request.POST.get('password')
            if password:
                user.set_password(password)
            user.save()
            messages.success(request, f'User "{user.username}" created successfully.')
            return redirect('user_list')
    else:
        form = FTPUserForm()
    return render(request, 'ftpmanager/user_form.html', {'form': form, 'title': 'Create User'})


@login_required
def user_edit(request, pk):
    user = get_object_or_404(FTPUser, pk=pk)
    if request.method == 'POST':
        form = FTPUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User "{user.username}" updated successfully.')
            return redirect('user_list')
    else:
        form = FTPUserForm(instance=user)
    return render(request, 'ftpmanager/user_form.html', {'form': form, 'title': 'Edit User', 'user': user})


@login_required
def user_delete(request, pk):
    user = get_object_or_404(FTPUser, pk=pk)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" deleted successfully.')
        return redirect('user_list')
    return render(request, 'ftpmanager/user_confirm_delete.html', {'user': user})


@login_required
def user_access(request, pk):
    """Manage folder access for a specific user"""
    user = get_object_or_404(FTPUser, pk=pk)
    folders = Folder.objects.all()
    current_access = {fa.folder_id: fa.permission for fa in user.folder_access.all()}

    if request.method == 'POST':
        # Clear existing access
        user.folder_access.all().delete()

        # Set new access
        for folder in folders:
            permission = request.POST.get(f'folder_{folder.id}')
            if permission and permission != 'none':
                FolderAccess.objects.create(user=user, folder=folder, permission=permission)

        messages.success(request, f'Access permissions for "{user.username}" updated.')
        return redirect('user_list')

    return render(request, 'ftpmanager/user_access.html', {
        'user': user,
        'folders': folders,
        'current_access': current_access,
    })


# Folder Views
@login_required
def folder_list(request):
    folders = Folder.objects.prefetch_related('user_access__user').all()
    return render(request, 'ftpmanager/folder_list.html', {'folders': folders})


@login_required
def folder_create(request):
    if request.method == 'POST':
        form = FolderForm(request.POST)
        if form.is_valid():
            folder = form.save()
            messages.success(request, f'Folder "{folder.name}" created successfully.')
            return redirect('folder_list')
    else:
        form = FolderForm()
    return render(request, 'ftpmanager/folder_form.html', {'form': form, 'title': 'Create Folder'})


@login_required
def folder_edit(request, pk):
    folder = get_object_or_404(Folder, pk=pk)
    if request.method == 'POST':
        form = FolderForm(request.POST, instance=folder)
        if form.is_valid():
            form.save()
            messages.success(request, f'Folder "{folder.name}" updated successfully.')
            return redirect('folder_list')
    else:
        form = FolderForm(instance=folder)
    return render(request, 'ftpmanager/folder_form.html', {'form': form, 'title': 'Edit Folder', 'folder': folder})


@login_required
def folder_delete(request, pk):
    folder = get_object_or_404(Folder, pk=pk)
    if request.method == 'POST':
        name = folder.name
        folder.delete()
        messages.success(request, f'Folder "{name}" deleted successfully.')
        return redirect('folder_list')
    return render(request, 'ftpmanager/folder_confirm_delete.html', {'folder': folder})


# Config Generation Views
@login_required
def generate_config(request):
    """Show config generation page with preview"""
    config = generate_proftpd_config()
    ftpusers = generate_ftpusers_file()
    return render(request, 'ftpmanager/generate_config.html', {
        'config': config,
        'ftpusers': ftpusers,
    })


@login_required
def download_config(request):
    """Download proftpd.conf file"""
    config = generate_proftpd_config()
    response = HttpResponse(config, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="proftpd.conf"'
    return response


@login_required
def download_ftpusers(request):
    """Download ftpd.passwd file for virtual users"""
    ftpusers = generate_ftpusers_file()
    response = HttpResponse(ftpusers, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="ftpd.passwd"'
    return response


# Profile Settings
@login_required
def profile_settings(request):
    """Edit user profile settings (basedir, exclude_dirs)"""
    # Get or create profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings saved successfully.')
            return redirect('profile_settings')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'ftpmanager/profile_settings.html', {'form': form})


# Directory Lookup API
@login_required
def list_directories(request):
    """AJAX endpoint to list directories for folder lookup"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    basedir = profile.basedir
    exclude_list = profile.get_exclude_list()
    max_depth = 4

    directories = []

    if not os.path.isdir(basedir):
        return JsonResponse({'error': f'Base directory not found: {basedir}', 'directories': []})

    def should_exclude(path):
        """Check if path should be excluded"""
        for exclude in exclude_list:
            if exclude in path:
                return True
        return False

    def scan_dirs(base, current_depth=0):
        """Recursively scan directories up to max_depth"""
        if current_depth >= max_depth:
            return

        try:
            entries = os.listdir(base)
        except PermissionError:
            return

        for entry in sorted(entries):
            full_path = os.path.join(base, entry)

            if not os.path.isdir(full_path):
                continue

            if should_exclude(full_path):
                continue

            directories.append(full_path)
            scan_dirs(full_path, current_depth + 1)

    scan_dirs(basedir)

    return JsonResponse({
        'basedir': basedir,
        'directories': directories
    })
