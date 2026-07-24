from django import forms
from django.utils.translation import gettext_lazy as _
from .models import EventoCalendario


class EventoForm(forms.ModelForm):
    class Meta:
        model = EventoCalendario
        fields = ['titulo', 'descricao', 'data_inicio', 'data_fim', 'dia_inteiro', 'visibilidade', 'cor']
        labels = {
            'titulo': _('Título'),
            'descricao': _('Descrição'),
            'data_inicio': _('Início'),
            'data_fim': _('Fim'),
            'dia_inteiro': _('Dia inteiro'),
            'visibilidade': _('Visibilidade'),
            'cor': _('Cor'),
        }
        widgets = {
            'data_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'data_fim': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'cor': forms.TextInput(attrs={'type': 'color'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descricao'].required = False
        self.fields['data_fim'].required = False
