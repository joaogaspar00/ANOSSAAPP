from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Despesa, Liquidacao, CATEGORIAS, DIVISAO_CHOICES


class DespesaForm(forms.ModelForm):
    class Meta:
        model = Despesa
        fields = ['descricao', 'valor', 'categoria', 'data', 'pago_por', 'divisao', 'valor_pessoa_a', 'valor_pessoa_b', 'notas']
        labels = {
            'descricao': _('Descrição'),
            'valor': _('Valor total'),
            'categoria': _('Categoria'),
            'data': _('Data'),
            'pago_por': _('Pago por'),
            'divisao': _('Divisão'),
            'valor_pessoa_a': _('Valor — Pessoa A'),
            'valor_pessoa_b': _('Valor — Pessoa B'),
            'notas': _('Notas'),
        }
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'notas': forms.Textarea(attrs={'rows': 2}),
            'valor_pessoa_a': forms.NumberInput(attrs={'step': '0.01'}),
            'valor_pessoa_b': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, household=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if household:
            membros = household.membros()
            self.fields['pago_por'].queryset = membros
            self.fields['pago_por'].initial = user
        self.fields['valor_pessoa_a'].required = False
        self.fields['valor_pessoa_b'].required = False

    def clean(self):
        cleaned = super().clean()
        divisao = cleaned.get('divisao')
        valor = cleaned.get('valor')
        if divisao == 'personalizado' and valor:
            a = cleaned.get('valor_pessoa_a') or 0
            b = cleaned.get('valor_pessoa_b') or 0
            if abs(float(a) + float(b) - float(valor)) > 0.01:
                raise forms.ValidationError(_('A soma dos valores personalizados deve ser igual ao valor total.'))
        return cleaned


class LiquidacaoForm(forms.ModelForm):
    class Meta:
        model = Liquidacao
        fields = ['valor', 'notas']
        labels = {
            'valor': _('Valor a liquidar'),
            'notas': _('Notas'),
        }
        widgets = {
            'valor': forms.NumberInput(attrs={'step': '0.01'}),
            'notas': forms.Textarea(attrs={'rows': 2}),
        }
