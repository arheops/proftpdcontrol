from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Users
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:pk>/access/', views.user_access, name='user_access'),

    # Folders
    path('folders/', views.folder_list, name='folder_list'),
    path('folders/create/', views.folder_create, name='folder_create'),
    path('folders/<int:pk>/edit/', views.folder_edit, name='folder_edit'),
    path('folders/<int:pk>/delete/', views.folder_delete, name='folder_delete'),

    # Config generation
    path('config/', views.generate_config, name='generate_config'),
    path('config/download/', views.download_config, name='download_config'),
    path('config/download-users/', views.download_ftpusers, name='download_ftpusers'),
]
