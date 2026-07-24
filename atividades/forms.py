from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Atividade


class AtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = ['nome', 'tipo', 'estado', 'data_planeada', 'data_realizada', 'localizacao', 'notas']
        labels = {
            'nome': _('Nome'),
            'tipo': _('Tipo'),
            'estado': _('Estado'),
            'data_planeada': _('Data planeada'),
            'data_realizada': _('Data realizada'),
            'localizacao': _('Localização'),
            'notas': _('Notas'),
        }
        widgets = {
            'data_planeada': forms.DateInput(attrs={'type': 'date'}),
            'data_realizada': forms.DateInput(attrs={'type': 'date'}),
            'notas': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ['data_planeada', 'data_realizada', 'localizacao', 'notas']:
            self.fields[f].required = False


class AvaliacaoForm(forms.Form):
    avaliacao = forms.IntegerField(min_value=1, max_value=5, label=_('Avaliação (1-5 estrelas)'))
