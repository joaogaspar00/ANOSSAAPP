from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from core.models import Household


VISIBILIDADE_CHOICES = [
    ('partilhado', _('Partilhado')),
    ('pessoal', _('Pessoal')),
]


class EventoCalendario(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='eventos')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField(null=True, blank=True)
    dia_inteiro = models.BooleanField(default=False)
    visibilidade = models.CharField(max_length=20, choices=VISIBILIDADE_CHOICES, default='partilhado')
    pertence_a = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eventos_pessoais')
    cor = models.CharField(max_length=7, default='#5C6BC0')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eventos_criados')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['data_inicio']

    def __str__(self):
        return self.titulo

    def visivel_para(self, user):
        if self.visibilidade == 'partilhado':
            return True
        return self.pertence_a == user
