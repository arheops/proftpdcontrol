from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.html import format_html
from .models import FTPUser, Folder, FolderAccess, UserProfile


# Customize admin site
admin.site.site_header = 'ProFTPD Control Administration'
admin.site.site_title = 'ProFTPD Admin'
admin.site.index_title = format_html(
    'Administration &nbsp; | &nbsp; <a href="/users/" style="color: #447e9b;">Go to FTP Control Panel</a>'
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile Settings'
    fields = ['basedir', 'exclude_dirs', 'systemuser_regexp']


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]


# Unregister the default User admin and register with inline
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(FTPUser)
class FTPUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'systemuser', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['username', 'systemuser']


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ['name', 'path', 'created_at']
    search_fields = ['name', 'path']


@admin.register(FolderAccess)
class FolderAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'folder', 'permission', 'created_at']
    list_filter = ['permission']
    search_fields = ['user__username', 'folder__name']
