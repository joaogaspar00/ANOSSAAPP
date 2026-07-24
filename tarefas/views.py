from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Tarefa, RegraRecorrencia
from .forms import TarefaForm, RegraRecorrenciaForm


def household_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.profile.household:
            messages.error(request, 'Precisas de pertencer a um casal primeiro.')
            return redirect('onboarding')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return login_required(wrapper)


@household_required
def lista_tarefas(request):
    household = request.user.profile.household
    filtro = request.GET.get('filtro', 'todas')
    parceiro = household.parceiro(request.user)

    tarefas = Tarefa.objects.filter(household=household).select_related(
        'atribuida_a', 'atribuida_a__profile', 'created_by', 'created_by__profile'
    )

    if filtro == 'minhas':
        tarefas = tarefas.filter(atribuida_a=request.user)
    elif filtro == 'parceiro' and parceiro:
        tarefas = tarefas.filter(atribuida_a=parceiro)
    elif filtro == 'concluidas':
        tarefas = tarefas.filter(estado='concluida')
    elif filtro != 'todas':
        tarefas = tarefas.exclude(estado='concluida')

    if filtro not in ['concluidas', 'todas']:
        tarefas = tarefas.exclude(estado='concluida')

    pendentes = tarefas.filter(estado='pendente').order_by('data_limite', 'titulo')
    em_curso = tarefas.filter(estado='em_curso').order_by('data_limite', 'titulo')
    concluidas = tarefas.filter(estado='concluida').order_by('-concluida_em')[:20] if filtro == 'concluidas' else []

    ctx = {
        'pendentes': pendentes,
        'em_curso': em_curso,
        'concluidas': concluidas,
        'filtro': filtro,
        'parceiro': parceiro,
        'household': household,
    }
    return render(request, 'tarefas/lista.html', ctx)


@household_required
def criar_tarefa(request):
    household = request.user.profile.household
    if request.method == 'POST':
        form = TarefaForm(request.POST, household=household)
        regra_form = RegraRecorrenciaForm(request.POST)
        if form.is_valid():
            tarefa = form.save(commit=False)
            tarefa.household = household
            tarefa.created_by = request.user
            if tarefa.recorrente and regra_form.is_valid():
                regra = regra_form.save()
                tarefa.regra_recorrencia = regra
            tarefa.save()
            messages.success(request, 'Tarefa criada.')
            return redirect('lista_tarefas')
    else:
        form = TarefaForm(household=household)
        regra_form = RegraRecorrenciaForm()
    return render(request, 'tarefas/form_tarefa.html', {
        'form': form, 'regra_form': regra_form, 'titulo': 'Nova Tarefa'
    })


@household_required
def editar_tarefa(request, pk):
    household = request.user.profile.household
    tarefa = get_object_or_404(Tarefa, pk=pk, household=household)
    if request.method == 'POST':
        form = TarefaForm(request.POST, instance=tarefa, household=household)
        regra_form = RegraRecorrenciaForm(request.POST, instance=tarefa.regra_recorrencia)
        if form.is_valid():
            tarefa = form.save(commit=False)
            if tarefa.recorrente and regra_form.is_valid():
                regra = regra_form.save()
                tarefa.regra_recorrencia = regra
            tarefa.save()
            messages.success(request, 'Tarefa atualizada.')
            return redirect('lista_tarefas')
    else:
        form = TarefaForm(instance=tarefa, household=household)
        regra_form = RegraRecorrenciaForm(instance=tarefa.regra_recorrencia)
    return render(request, 'tarefas/form_tarefa.html', {
        'form': form, 'regra_form': regra_form, 'titulo': 'Editar Tarefa', 'tarefa': tarefa
    })


@household_required
def concluir_tarefa(request, pk):
    household = request.user.profile.household
    tarefa = get_object_or_404(Tarefa, pk=pk, household=household)
    tarefa.concluir(request.user)
    messages.success(request, f'"{tarefa.titulo}" marcada como concluída.')
    return redirect(request.META.get('HTTP_REFERER', 'lista_tarefas'))


@household_required
def mover_estado(request, pk):
    household = request.user.profile.household
    tarefa = get_object_or_404(Tarefa, pk=pk, household=household)
    novo_estado = request.POST.get('estado')
    if novo_estado in ['pendente', 'em_curso', 'concluida']:
        if novo_estado == 'concluida':
            tarefa.concluir(request.user)
        else:
            tarefa.estado = novo_estado
            tarefa.save()
        messages.success(request, 'Estado atualizado.')
    return redirect(request.META.get('HTTP_REFERER', 'lista_tarefas'))


@household_required
def eliminar_tarefa(request, pk):
    household = request.user.profile.household
    tarefa = get_object_or_404(Tarefa, pk=pk, household=household)
    if request.method == 'POST':
        tarefa.delete()
        messages.success(request, 'Tarefa eliminada.')
        return redirect('lista_tarefas')
    return render(request, 'tarefas/confirmar_eliminar.html', {'objeto': tarefa, 'tipo': 'tarefa'})
