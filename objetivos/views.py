from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Objetivo
from .forms import ObjetivoForm, AtualizarProgressoForm


def household_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.profile.household:
            messages.error(request, 'Precisas de pertencer a um casal primeiro.')
            return redirect('onboarding')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return login_required(wrapper)


@household_required
def lista_objetivos(request):
    household = request.user.profile.household
    filtro = request.GET.get('estado', 'ativo')

    objetivos = Objetivo.objects.filter(household=household).select_related(
        'created_by', 'created_by__profile'
    )
    if filtro:
        objetivos = objetivos.filter(estado=filtro)

    ctx = {
        'objetivos': objetivos,
        'filtro': filtro,
        'household': household,
    }
    return render(request, 'objetivos/lista.html', ctx)


@household_required
def criar_objetivo(request):
    household = request.user.profile.household
    if request.method == 'POST':
        form = ObjetivoForm(request.POST)
        if form.is_valid():
            objetivo = form.save(commit=False)
            objetivo.household = household
            objetivo.created_by = request.user
            objetivo.save()
            messages.success(request, 'Objetivo criado.')
            return redirect('lista_objetivos')
    else:
        form = ObjetivoForm()
    return render(request, 'objetivos/form_objetivo.html', {'form': form, 'titulo': 'Novo Objetivo'})


@household_required
def editar_objetivo(request, pk):
    household = request.user.profile.household
    objetivo = get_object_or_404(Objetivo, pk=pk, household=household)
    if request.method == 'POST':
        form = ObjetivoForm(request.POST, instance=objetivo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Objetivo atualizado.')
            return redirect('lista_objetivos')
    else:
        form = ObjetivoForm(instance=objetivo)
    return render(request, 'objetivos/form_objetivo.html', {
        'form': form, 'titulo': 'Editar Objetivo', 'objetivo': objetivo
    })


@household_required
def atualizar_progresso(request, pk):
    household = request.user.profile.household
    objetivo = get_object_or_404(Objetivo, pk=pk, household=household)
    if request.method == 'POST':
        form = AtualizarProgressoForm(request.POST)
        if form.is_valid():
            objetivo.valor_atual = form.cleaned_data['valor_atual']
            objetivo.save()
            messages.success(request, 'Progresso atualizado.')
            return redirect('lista_objetivos')
    else:
        form = AtualizarProgressoForm(initial={'valor_atual': objetivo.valor_atual})
    return render(request, 'objetivos/atualizar_progresso.html', {'form': form, 'objetivo': objetivo})


@household_required
def eliminar_objetivo(request, pk):
    household = request.user.profile.household
    objetivo = get_object_or_404(Objetivo, pk=pk, household=household)
    if request.method == 'POST':
        objetivo.delete()
        messages.success(request, 'Objetivo eliminado.')
        return redirect('lista_objetivos')
    return render(request, 'objetivos/confirmar_eliminar.html', {'objeto': objetivo, 'tipo': 'objetivo'})
