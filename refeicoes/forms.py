from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Refeicao, Ingrediente, InventarioItem, ItemListaCompras


class RefeicaoForm(forms.ModelForm):
    class Meta:
        model = Refeicao
        fields = ['nome', 'data', 'tipo', 'receita', 'notas']
        labels = {
            'nome': _('Nome da refeição'),
            'data': _('Data'),
            'tipo': _('Tipo'),
            'receita': _('Receita / instruções'),
            'notas': _('Notas'),
        }
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'receita': forms.Textarea(attrs={'rows': 5}),
            'notas': forms.Textarea(attrs={'rows': 2}),
        }


class InventarioItemForm(forms.ModelForm):
    class Meta:
        model = InventarioItem
        fields = ['ingrediente', 'quantidade', 'minimo_stock']
        labels = {
            'ingrediente': _('Ingrediente'),
            'quantidade': _('Quantidade em stock'),
            'minimo_stock': _('Stock mínimo'),
        }
        widgets = {
            'quantidade': forms.NumberInput(attrs={'step': '0.1'}),
            'minimo_stock': forms.NumberInput(attrs={'step': '0.1'}),
        }


class ItemListaComprasForm(forms.ModelForm):
    class Meta:
        model = ItemListaCompras
        fields = ['nome', 'quantidade', 'categoria']
        labels = {
            'nome': _('Item'),
            'quantidade': _('Quantidade'),
            'categoria': _('Categoria'),
        }


class IngredienteForm(forms.ModelForm):
    class Meta:
        model = Ingrediente
        fields = ['nome', 'unidade']
        labels = {
            'nome': _('Nome'),
            'unidade': _('Unidade'),
        }
