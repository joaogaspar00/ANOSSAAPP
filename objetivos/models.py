from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from core.models import Household


TIPO_CHOICES = [
    ('financeiro', _('Financeiro')),
    ('viagem', _('Viagem')),
    ('casa', _('Casa')),
    ('pessoal', _('Pessoal')),
    ('outro', _('Outro')),
]

ESTADO_CHOICES = [
    ('ativo', _('Ativo')),
    ('concluido', _('Concluído')),
    ('pausado', _('Pausado')),
]


class Objetivo(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='objetivos')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='outro')
    valor_meta = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    valor_atual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    data_limite = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ativo')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='objetivos_criados')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Objetivo'
        verbose_name_plural = 'Objetivos'
        ordering = ['-criado_em']

    def __str__(self):
        return self.titulo

    def percentagem(self):
        if not self.valor_meta or self.valor_meta == 0:
            return 0
        pct = (self.valor_atual / self.valor_meta) * 100
        return min(int(pct), 100)

    def valor_em_falta(self):
        if not self.valor_meta:
            return None
        return max(self.valor_meta - self.valor_atual, 0)

    def save(self, *args, **kwargs):
        if self.valor_meta and self.valor_atual >= self.valor_meta and self.estado == 'ativo':
            self.estado = 'concluido'
        super().save(*args, **kwargs)
