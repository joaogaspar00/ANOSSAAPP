from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Atividade
from .forms import AtividadeForm, AvaliacaoForm


def household_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.profile.household:
            messages.error(request, 'Precisas de pertencer a um casal primeiro.')
            return redirect('onboarding')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return login_required(wrapper)


@household_required
def lista_atividades(request):
    household = request.user.profile.household
    filtro_tipo = request.GET.get('tipo', '')
    filtro_estado = request.GET.get('estado', '')

    atividades = Atividade.objects.filter(household=household).select_related(
        'created_by', 'created_by__profile'
    )

    if filtro_tipo:
        atividades = atividades.filter(tipo=filtro_tipo)
    if filtro_estado:
        atividades = atividades.filter(estado=filtro_estado)

    from .models import TIPO_CHOICES, ESTADO_CHOICES
    ctx = {
        'atividades': atividades,
        'tipos': TIPO_CHOICES,
        'estados': ESTADO_CHOICES,
        'filtro_tipo': filtro_tipo,
        'filtro_estado': filtro_estado,
        'household': household,
    }
    return render(request, 'atividades/lista.html', ctx)


@household_required
def criar_atividade(request):
    household = request.user.profile.household
    if request.method == 'POST':
        form = AtividadeForm(request.POST)
        if form.is_valid():
            atividade = form.save(commit=False)
            atividade.household = household
            atividade.created_by = request.user
            atividade.save()
            messages.success(request, 'Atividade adicionada.')
            return redirect('lista_atividades')
    else:
        form = AtividadeForm()
    return render(request, 'atividades/form_atividade.html', {'form': form, 'titulo': 'Nova Atividade'})


@household_required
def editar_atividade(request, pk):
    household = request.user.profile.household
    atividade = get_object_or_404(Atividade, pk=pk, household=household)
    if request.method == 'POST':
        form = AtividadeForm(request.POST, instance=atividade)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atividade atualizada.')
            return redirect('lista_atividades')
    else:
        form = AtividadeForm(instance=atividade)
    return render(request, 'atividades/form_atividade.html', {
        'form': form, 'titulo': 'Editar Atividade', 'atividade': atividade
    })


@household_required
def eliminar_atividade(request, pk):
    household = request.user.profile.household
    atividade = get_object_or_404(Atividade, pk=pk, household=household)
    if request.method == 'POST':
        atividade.delete()
        messages.success(request, 'Atividade eliminada.')
        return redirect('lista_atividades')
    return render(request, 'atividades/confirmar_eliminar.html', {'objeto': atividade, 'tipo': 'atividade'})


@household_required
def avaliar_atividade(request, pk):
    household = request.user.profile.household
    atividade = get_object_or_404(Atividade, pk=pk, household=household, estado='feito')
    if request.method == 'POST':
        form = AvaliacaoForm(request.POST)
        if form.is_valid():
            atividade.definir_avaliacao(request.user, form.cleaned_data['avaliacao'])
            messages.success(request, 'Avaliação guardada.')
            return redirect('lista_atividades')
    else:
        avaliacao_atual = atividade.avaliacao_para_user(request.user)
        form = AvaliacaoForm(initial={'avaliacao': avaliacao_atual})
    return render(request, 'atividades/avaliar.html', {'form': form, 'atividade': atividade})


@household_required
def mover_estado_atividade(request, pk):
    household = request.user.profile.household
    atividade = get_object_or_404(Atividade, pk=pk, household=household)
    novo_estado = request.POST.get('estado')
    if novo_estado in ['wishlist', 'planeado', 'feito']:
        atividade.estado = novo_estado
        if novo_estado == 'feito' and not atividade.data_realizada:
            from django.utils import timezone
            atividade.data_realizada = timezone.now().date()
        atividade.save()
        messages.success(request, 'Estado atualizado.')
    return redirect('lista_atividades')
