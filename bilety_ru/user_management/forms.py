from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Обязательное поле. Введите действующий email адрес.')
    first_name = forms.CharField(required=True, help_text='Обязательное поле.')
    last_name = forms.CharField(required=True, help_text='Обязательное поле.')
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email


class SignInForm(AuthenticationForm):
    username = forms.CharField(label='Имя пользователя')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput())
    
    class Meta:
        model = User
        fields = ('username', 'password')
