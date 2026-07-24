from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid


class Household(models.Model):
    nome = models.CharField(max_length=100)
    criado_em = models.DateTimeField(auto_now_add=True)
    token_convite = models.UUIDField(default=uuid.uuid4, unique=True)
    convite_ativo = models.BooleanField(default=True)
    moeda = models.CharField(max_length=10, default='DKK')

    class Meta:
        verbose_name = 'Household'
        verbose_name_plural = 'Households'

    def __str__(self):
        return self.nome

    def membros(self):
        return User.objects.filter(profile__household=self).select_related('profile')

    def parceiro(self, user):
        return User.objects.filter(profile__household=self).exclude(pk=user.pk).select_related('profile').first()

    def esta_completo(self):
        return self.membros().count() >= 2

    def simbolo_moeda(self):
        simbolos = {'DKK': 'kr', 'EUR': '€', 'USD': '$', 'GBP': '£', 'SEK': 'kr', 'NOK': 'kr'}
        return simbolos.get(self.moeda, self.moeda)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    household = models.ForeignKey(Household, null=True, blank=True, on_delete=models.SET_NULL, related_name='profiles')
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    cor_perfil = models.CharField(max_length=7, default='#5C6BC0')
    bio = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'

    def __str__(self):
        return f'Perfil de {self.user.get_full_name() or self.user.username}'

    def nome_display(self):
        return self.user.get_full_name() or self.user.username

    def iniciais(self):
        nome = self.nome_display()
        partes = nome.split()
        if len(partes) >= 2:
            return f'{partes[0][0]}{partes[1][0]}'.upper()
        return nome[:2].upper()


@receiver(post_save, sender=User)
def criar_perfil(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def guardar_perfil(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
