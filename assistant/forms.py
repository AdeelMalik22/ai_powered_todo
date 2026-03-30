"""
Forms for CRUD operations on todos, notes, and vault entries.
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from assistant.models import Todo, Note, VaultEntry
from assistant.services.encryption_service import get_encryption_service


class CustomUserCreationForm(UserCreationForm):
    """Custom user registration form."""
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class TodoForm(forms.ModelForm):
    """Form for creating/editing todos."""
    class Meta:
        model = Todo
        fields = ('title', 'description', 'status')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Todo title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Description'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class NoteForm(forms.ModelForm):
    """Form for creating/editing notes."""
    class Meta:
        model = Note
        fields = ('title', 'content')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Note title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'Note content'}),
        }


class VaultEntryForm(forms.Form):
    """Form for creating/editing vault entries."""
    label = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Label (optional)'}),
        label='Label'
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        label='Email'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        label='Password'
    )

    def save_to_vault_entry(self, user):
        """Encrypt and create a VaultEntry instance."""
        encryption_service = get_encryption_service()

        email_encrypted = encryption_service.encrypt(self.cleaned_data['email'])
        password_encrypted = encryption_service.encrypt(self.cleaned_data['password'])

        vault_entry = VaultEntry(
            user=user,
            label=self.cleaned_data.get('label', ''),
            email_encrypted=email_encrypted,
            password_encrypted=password_encrypted,
        )
        vault_entry.save()
        return vault_entry

