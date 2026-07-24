from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Objetivo


class ObjetivoForm(forms.ModelForm):
    class Meta:
        model = Objetivo
        fields = ['titulo', 'descricao', 'tipo', 'valor_meta', 'valor_atual', 'data_limite', 'estado']
        labels = {
            'titulo': _('Título'),
            'descricao': _('Descrição'),
            'tipo': _('Tipo'),
            'valor_meta': _('Valor meta'),
            'valor_atual': _('Valor atual'),
            'data_limite': _('Data limite'),
            'estado': _('Estado'),
        }
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'data_limite': forms.DateInput(attrs={'type': 'date'}),
            'valor_meta': forms.NumberInput(attrs={'step': '0.01'}),
            'valor_atual': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ['descricao', 'valor_meta', 'valor_atual', 'data_limite']:
            self.fields[f].required = False


class AtualizarProgressoForm(forms.Form):
    valor_atual = forms.DecimalField(
        max_digits=12, decimal_places=2,
        label=_('Valor atual'),
        widget=forms.NumberInput(attrs={'step': '0.01'})
    )
