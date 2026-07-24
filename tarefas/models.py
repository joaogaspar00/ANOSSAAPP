from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from core.models import Household


ESTADO_CHOICES = [
    ('pendente', _('Pendente')),
    ('em_curso', _('Em curso')),
    ('concluida', _('Concluída')),
]

PRIORIDADE_CHOICES = [
    ('baixa', _('Baixa')),
    ('media', _('Média')),
    ('alta', _('Alta')),
]

FREQUENCIA_CHOICES = [
    ('diaria', _('Diária')),
    ('semanal', _('Semanal')),
    ('mensal', _('Mensal')),
    ('anual', _('Anual')),
]


class RegraRecorrencia(models.Model):
    frequencia = models.CharField(max_length=20, choices=FREQUENCIA_CHOICES)
    intervalo = models.PositiveIntegerField(default=1)
    dia_semana = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Regra de Recorrência'
        verbose_name_plural = 'Regras de Recorrência'

    def __str__(self):
        return f'{self.get_frequencia_display()} (cada {self.intervalo})'


class Tarefa(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='tarefas')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    atribuida_a = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='tarefas_atribuidas')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendente')
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='media')
    data_limite = models.DateField(null=True, blank=True)
    recorrente = models.BooleanField(default=False)
    regra_recorrencia = models.ForeignKey(RegraRecorrencia, null=True, blank=True, on_delete=models.SET_NULL)
    concluida_por = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='tarefas_concluidas')
    concluida_em = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tarefas_criadas')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tarefa'
        verbose_name_plural = 'Tarefas'
        ordering = ['-prioridade', 'data_limite', 'titulo']

    def __str__(self):
        return self.titulo

    def concluir(self, user):
        self.estado = 'concluida'
        self.concluida_por = user
        self.concluida_em = timezone.now()
        self.save()
        if self.recorrente and self.regra_recorrencia:
            self._gerar_proxima()

    def _gerar_proxima(self):
        regra = self.regra_recorrencia
        nova_data = self.data_limite
        if nova_data:
            if regra.frequencia == 'diaria':
                nova_data = nova_data + timedelta(days=regra.intervalo)
            elif regra.frequencia == 'semanal':
                nova_data = nova_data + timedelta(weeks=regra.intervalo)
            elif regra.frequencia == 'mensal':
                from dateutil.relativedelta import relativedelta
                nova_data = nova_data + relativedelta(months=regra.intervalo)
            elif regra.frequencia == 'anual':
                from dateutil.relativedelta import relativedelta
                nova_data = nova_data + relativedelta(years=regra.intervalo)

        Tarefa.objects.create(
            household=self.household,
            titulo=self.titulo,
            descricao=self.descricao,
            atribuida_a=self.atribuida_a,
            estado='pendente',
            prioridade=self.prioridade,
            data_limite=nova_data,
            recorrente=True,
            regra_recorrencia=regra,
            created_by=self.created_by,
        )

    def esta_atrasada(self):
        from django.utils import timezone
        if self.data_limite and self.estado != 'concluida':
            return self.data_limite < timezone.now().date()
        return False
