from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from core.models import Household


CATEGORIAS = [
    ('alimentacao', _('Alimentação')),
    ('transportes', _('Transportes')),
    ('casa', _('Casa')),
    ('saude', _('Saúde')),
    ('lazer', _('Lazer')),
    ('vestuario', _('Vestuário')),
    ('viagem', _('Viagem')),
    ('subscricoes', _('Subscrições')),
    ('outro', _('Outro')),
]

DIVISAO_CHOICES = [
    ('50_50', '50/50'),
    ('total_a', _('Pago por mim (total)')),
    ('total_b', _('Pago pelo parceiro (total)')),
    ('personalizado', _('Personalizado')),
]


class Despesa(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='despesas')
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, default='outro')
    data = models.DateField()
    pago_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='despesas_pagas')
    divisao = models.CharField(max_length=20, choices=DIVISAO_CHOICES, default='50_50')
    valor_pessoa_a = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_pessoa_b = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notas = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='despesas_criadas')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Despesa'
        verbose_name_plural = 'Despesas'
        ordering = ['-data', '-criado_em']

    def __str__(self):
        return f'{self.descricao} — {self.valor} {self.household.moeda}'

    def calcular_divisao(self):
        membros = list(self.household.membros())
        if len(membros) < 2:
            return
        if self.divisao == '50_50':
            metade = self.valor / 2
            self.valor_pessoa_a = metade
            self.valor_pessoa_b = metade
        elif self.divisao == 'total_a':
            self.valor_pessoa_a = self.valor
            self.valor_pessoa_b = 0
        elif self.divisao == 'total_b':
            self.valor_pessoa_a = 0
            self.valor_pessoa_b = self.valor

    def save(self, *args, **kwargs):
        if self.divisao != 'personalizado':
            self.calcular_divisao()
        super().save(*args, **kwargs)


class Liquidacao(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='liquidacoes')
    de = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liquidacoes_enviadas')
    para = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liquidacoes_recebidas')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField(auto_now_add=True)
    notas = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Liquidação'
        verbose_name_plural = 'Liquidações'
        ordering = ['-data']

    def __str__(self):
        return f'{self.de.username} → {self.para.username}: {self.valor}'
