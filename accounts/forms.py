from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

User = get_user_model()


class RegisterForm(forms.Form):
    email = forms.CharField(max_length=254)
    password = forms.CharField(min_length=6)
    confirm_password = forms.CharField()

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        try:
            validate_email(email)
        except ValidationError:
            raise forms.ValidationError('Saisissez une adresse e-mail valide')
        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError('Un compte existe déjà avec cet e-mail')
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        if password and len(password) < 6:
            self.add_error('password', 'Le mot de passe doit contenir au moins 6 caractères')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', 'Les mots de passe ne correspondent pas')
        return cleaned


class LoginForm(forms.Form):
    email = forms.CharField(max_length=254)
    password = forms.CharField()

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()
