from django import forms
from .models import FTPUser, Folder, FolderAccess


class FTPUserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Leave blank to keep current password"
    )

    class Meta:
        model = FTPUser
        fields = ['username', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name', 'path', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'path': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '/path/to/folder'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class FolderAccessForm(forms.ModelForm):
    class Meta:
        model = FolderAccess
        fields = ['user', 'folder', 'permission']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'folder': forms.Select(attrs={'class': 'form-select'}),
            'permission': forms.Select(attrs={'class': 'form-select'}),
        }


class BulkAccessForm(forms.Form):
    """Form for setting multiple folder permissions for a user at once"""
    user = forms.ModelChoiceField(
        queryset=FTPUser.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for folder in Folder.objects.all():
            self.fields[f'folder_{folder.id}'] = forms.ChoiceField(
                choices=[('none', 'No Access'), ('read', 'Read Only'), ('write', 'Read & Write')],
                required=False,
                label=folder.name,
                widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
            )
