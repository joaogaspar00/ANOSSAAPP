from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from core.models import Household


TIPO_CHOICES = [
    ('restaurante', _('Restaurante')),
    ('museu', _('Museu / Exposição')),
    ('concerto', _('Concerto / Espetáculo')),
    ('viagem', _('Viagem')),
    ('cinema', _('Cinema')),
    ('desporto', _('Desporto')),
    ('natureza', _('Natureza / Outdoor')),
    ('outro', _('Outro')),
]

ESTADO_CHOICES = [
    ('wishlist', 'Wishlist'),
    ('planeado', _('Planeado')),
    ('feito', _('Feito')),
]


class Atividade(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='atividades')
    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='outro')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='wishlist')
    data_planeada = models.DateField(null=True, blank=True)
    data_realizada = models.DateField(null=True, blank=True)
    localizacao = models.CharField(max_length=200, blank=True)
    notas = models.TextField(blank=True)
    avaliacao_a = models.IntegerField(null=True, blank=True)
    avaliacao_b = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='atividades_criadas')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Atividade'
        verbose_name_plural = 'Atividades'
        ordering = ['-criado_em']

    def __str__(self):
        return self.nome

    def avaliacao_media(self):
        avaliacoes = [a for a in [self.avaliacao_a, self.avaliacao_b] if a is not None]
        if not avaliacoes:
            return None
        return sum(avaliacoes) / len(avaliacoes)

    def avaliacao_para_user(self, user):
        membros = list(self.household.membros())
        if not membros:
            return None
        if user == membros[0]:
            return self.avaliacao_a
        return self.avaliacao_b

    def definir_avaliacao(self, user, valor):
        membros = list(self.household.membros())
        if not membros:
            return
        if user == membros[0]:
            self.avaliacao_a = valor
        else:
            self.avaliacao_b = valor
        self.save()
