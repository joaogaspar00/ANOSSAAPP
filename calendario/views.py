from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, date
import calendar
from .models import EventoCalendario
from .forms import EventoForm


def household_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.profile.household:
            messages.error(request, 'Precisas de pertencer a um casal primeiro.')
            return redirect('onboarding')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return login_required(wrapper)


@household_required
def calendario_mensal(request):
    household = request.user.profile.household
    hoje = timezone.now().date()

    try:
        ano = int(request.GET.get('ano', hoje.year))
        mes = int(request.GET.get('mes', hoje.month))
    except ValueError:
        ano, mes = hoje.year, hoje.month

    if mes < 1:
        mes = 12
        ano -= 1
    elif mes > 12:
        mes = 1
        ano += 1

    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])
    mes_anterior = (primeiro_dia - timedelta(days=1))
    mes_seguinte = (ultimo_dia + timedelta(days=1))

    cal = calendar.monthcalendar(ano, mes)

    eventos = EventoCalendario.objects.filter(
        household=household,
        data_inicio__date__range=(primeiro_dia, ultimo_dia),
    ).select_related('pertence_a', 'pertence_a__profile', 'created_by')

    eventos_visiveis = [e for e in eventos if e.visivel_para(request.user)]

    eventos_por_dia = {}
    for evento in eventos_visiveis:
        dia = evento.data_inicio.date().day
        if dia not in eventos_por_dia:
            eventos_por_dia[dia] = []
        eventos_por_dia[dia].append(evento)

    ctx = {
        'ano': ano,
        'mes': mes,
        'mes_nome': ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                     'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][mes],
        'cal': cal,
        'hoje': hoje,
        'eventos_por_dia': eventos_por_dia,
        'mes_anterior': mes_anterior,
        'mes_seguinte': mes_seguinte,
        'household': household,
    }
    return render(request, 'calendario/mensal.html', ctx)


@household_required
def criar_evento(request):
    household = request.user.profile.household
    if request.method == 'POST':
        form = EventoForm(request.POST)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.household = household
            evento.pertence_a = request.user
            evento.created_by = request.user
            evento.save()
            messages.success(request, 'Evento criado.')
            return redirect('calendario')
    else:
        data_inicial = request.GET.get('data')
        initial = {}
        if data_inicial:
            initial['data_inicio'] = f'{data_inicial}T09:00'
        form = EventoForm(initial=initial)
    return render(request, 'calendario/form_evento.html', {'form': form, 'titulo': 'Novo Evento'})


@household_required
def editar_evento(request, pk):
    household = request.user.profile.household
    evento = get_object_or_404(EventoCalendario, pk=pk, household=household)
    if request.method == 'POST':
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento atualizado.')
            return redirect('calendario')
    else:
        form = EventoForm(instance=evento)
    return render(request, 'calendario/form_evento.html', {
        'form': form, 'titulo': 'Editar Evento', 'evento': evento
    })


@household_required
def eliminar_evento(request, pk):
    household = request.user.profile.household
    evento = get_object_or_404(EventoCalendario, pk=pk, household=household)
    if request.method == 'POST':
        evento.delete()
        messages.success(request, 'Evento eliminado.')
        return redirect('calendario')
    return render(request, 'calendario/confirmar_eliminar.html', {'objeto': evento, 'tipo': 'evento'})


@household_required
def lista_eventos(request):
    household = request.user.profile.household
    hoje = timezone.now().date()
    eventos = EventoCalendario.objects.filter(
        household=household, data_inicio__date__gte=hoje
    ).order_by('data_inicio').select_related('pertence_a', 'pertence_a__profile')
    eventos_visiveis = [e for e in eventos if e.visivel_para(request.user)]
    return render(request, 'calendario/lista_eventos.html', {
        'eventos': eventos_visiveis, 'household': household, 'hoje': hoje
    })
