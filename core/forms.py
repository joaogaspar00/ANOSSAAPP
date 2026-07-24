from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile, Household


class RegistoForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, label='Nome próprio', required=True)
    last_name = forms.CharField(max_length=50, label='Apelido', required=True)
    email = forms.EmailField(label='Email', required=True)
    password1 = forms.CharField(label='Palavra-passe', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar palavra-passe', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']
        labels = {'username': 'Nome de utilizador'}

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este email já está em uso.')
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Nome de utilizador ou email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].label = 'Palavra-passe'


class HouseholdForm(forms.ModelForm):
    class Meta:
        model = Household
        fields = ['nome', 'moeda']
        labels = {
            'nome': 'Nome do casal',
            'moeda': 'Moeda',
        }
        widgets = {
            'moeda': forms.Select(choices=[
                ('DKK', 'Coroa Dinamarquesa (DKK)'),
                ('EUR', 'Euro (EUR)'),
                ('USD', 'Dólar Americano (USD)'),
                ('GBP', 'Libra Esterlina (GBP)'),
                ('SEK', 'Coroa Sueca (SEK)'),
                ('NOK', 'Coroa Norueguesa (NOK)'),
            ])
        }


class PerfilForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, label='Nome próprio', required=False)
    last_name = forms.CharField(max_length=50, label='Apelido', required=False)
    email = forms.EmailField(label='Email', required=False)

    class Meta:
        model = UserProfile
        fields = ['avatar', 'cor_perfil', 'bio']
        labels = {
            'avatar': 'Foto de perfil',
            'cor_perfil': 'Cor de perfil',
            'bio': 'Sobre mim',
        }
        widgets = {
            'cor_perfil': forms.TextInput(attrs={'type': 'color'}),
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def save_user_data(self, user):
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        email = self.cleaned_data.get('email', '')
        if email and email != user.email:
            if not User.objects.filter(email=email).exclude(pk=user.pk).exists():
                user.email = email
        user.save()
