from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Tarefa, RegraRecorrencia


class TarefaForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        fields = ['titulo', 'descricao', 'atribuida_a', 'prioridade', 'data_limite', 'recorrente']
        labels = {
            'titulo': _('Título'),
            'descricao': _('Descrição'),
            'atribuida_a': _('Atribuir a'),
            'prioridade': _('Prioridade'),
            'data_limite': _('Data limite'),
            'recorrente': _('Tarefa recorrente'),
        }
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'data_limite': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, household=None, **kwargs):
        super().__init__(*args, **kwargs)
        if household:
            self.fields['atribuida_a'].queryset = household.membros()
            self.fields['atribuida_a'].empty_label = _('Qualquer um')
        self.fields['atribuida_a'].required = False
        self.fields['data_limite'].required = False


class RegraRecorrenciaForm(forms.ModelForm):
    class Meta:
        model = RegraRecorrencia
        fields = ['frequencia', 'intervalo']
        labels = {
            'frequencia': _('Frequência'),
            'intervalo': _('Cada quantas unidades'),
        }
