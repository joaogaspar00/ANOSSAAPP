from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, date
from .models import Refeicao, InventarioItem, ItemListaCompras, Ingrediente
from .forms import RefeicaoForm, InventarioItemForm, ItemListaComprasForm


def household_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.profile.household:
            messages.error(request, 'Precisas de pertencer a um casal primeiro.')
            return redirect('onboarding')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return login_required(wrapper)


@household_required
def planeamento(request):
    household = request.user.profile.household
    hoje = timezone.now().date()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    dias = [inicio_semana + timedelta(days=i) for i in range(7)]

    refeicoes = Refeicao.objects.filter(
        household=household, data__range=(dias[0], dias[-1])
    ).select_related('created_by', 'created_by__profile')

    plano_dict = {dia: [] for dia in dias}
    for r in refeicoes:
        if r.data in plano_dict:
            plano_dict[r.data].append(r)

    plano = [(dia, plano_dict[dia]) for dia in dias]

    ctx = {
        'dias': dias,
        'plano': plano,
        'household': household,
        'hoje': hoje,
    }
    return render(request, 'refeicoes/planeamento.html', ctx)


@household_required
def criar_refeicao(request):
    household = request.user.profile.household
    data_inicial = request.GET.get('data')
    if request.method == 'POST':
        form = RefeicaoForm(request.POST)
        if form.is_valid():
            refeicao = form.save(commit=False)
            refeicao.household = household
            refeicao.created_by = request.user
            refeicao.save()
            messages.success(request, 'Refeição adicionada ao plano.')
            return redirect('planeamento')
    else:
        inicial = {'data': data_inicial} if data_inicial else {'data': timezone.now().date()}
        form = RefeicaoForm(initial=inicial)
    return render(request, 'refeicoes/form_refeicao.html', {'form': form, 'titulo': 'Adicionar Refeição'})


@household_required
def editar_refeicao(request, pk):
    household = request.user.profile.household
    refeicao = get_object_or_404(Refeicao, pk=pk, household=household)
    if request.method == 'POST':
        form = RefeicaoForm(request.POST, instance=refeicao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Refeição atualizada.')
            return redirect('planeamento')
    else:
        form = RefeicaoForm(instance=refeicao)
    return render(request, 'refeicoes/form_refeicao.html', {'form': form, 'titulo': 'Editar Refeição', 'refeicao': refeicao})


@household_required
def eliminar_refeicao(request, pk):
    household = request.user.profile.household
    refeicao = get_object_or_404(Refeicao, pk=pk, household=household)
    if request.method == 'POST':
        refeicao.delete()
        messages.success(request, 'Refeição removida.')
        return redirect('planeamento')
    return render(request, 'refeicoes/confirmar_eliminar.html', {'objeto': refeicao, 'tipo': 'refeição'})


@household_required
def lista_compras(request):
    household = request.user.profile.household
    itens = ItemListaCompras.objects.filter(household=household).select_related(
        'comprado_por', 'comprado_por__profile', 'created_by', 'created_by__profile'
    )
    itens_pendentes = itens.filter(comprado=False)
    itens_comprados = itens.filter(comprado=True)[:30]

    if request.method == 'POST':
        form = ItemListaComprasForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.household = household
            item.created_by = request.user
            item.save()
            messages.success(request, 'Item adicionado à lista.')
            return redirect('lista_compras')
    else:
        form = ItemListaComprasForm()

    ctx = {
        'itens_pendentes': itens_pendentes,
        'itens_comprados': itens_comprados,
        'form': form,
        'household': household,
    }
    return render(request, 'refeicoes/lista_compras.html', ctx)


@household_required
def marcar_comprado(request, pk):
    household = request.user.profile.household
    item = get_object_or_404(ItemListaCompras, pk=pk, household=household)
    item.comprado = not item.comprado
    if item.comprado:
        item.comprado_por = request.user
        item.comprado_em = timezone.now()
    else:
        item.comprado_por = None
        item.comprado_em = None
    item.save()
    return redirect('lista_compras')


@household_required
def eliminar_item_compras(request, pk):
    household = request.user.profile.household
    item = get_object_or_404(ItemListaCompras, pk=pk, household=household)
    if request.method == 'POST':
        item.delete()
    return redirect('lista_compras')


@household_required
def limpar_comprados(request):
    household = request.user.profile.household
    if request.method == 'POST':
        ItemListaCompras.objects.filter(household=household, comprado=True).delete()
        messages.success(request, 'Itens comprados removidos da lista.')
    return redirect('lista_compras')


@household_required
def inventario(request):
    household = request.user.profile.household
    itens = InventarioItem.objects.filter(household=household).select_related(
        'ingrediente', 'updated_by', 'updated_by__profile'
    )

    if request.method == 'POST':
        form = InventarioItemForm(request.POST)
        if form.is_valid():
            ingrediente = form.cleaned_data['ingrediente']
            item, created = InventarioItem.objects.get_or_create(
                household=household, ingrediente=ingrediente,
                defaults={'updated_by': request.user}
            )
            item.quantidade = form.cleaned_data['quantidade']
            item.minimo_stock = form.cleaned_data['minimo_stock']
            item.updated_by = request.user
            item.save()
            messages.success(request, 'Inventário atualizado.')
            return redirect('inventario')
    else:
        form = InventarioItemForm()

    ctx = {
        'itens': itens,
        'form': form,
        'household': household,
        'em_falta': itens.filter(quantidade__lte=0),
    }
    return render(request, 'refeicoes/inventario.html', ctx)


@household_required
def gerar_lista_compras(request):
    household = request.user.profile.household
    if request.method != 'POST':
        return redirect('lista_compras')

    hoje = timezone.now().date()
    fim_semana = hoje + timedelta(days=7)
    refeicoes = Refeicao.objects.filter(
        household=household, data__range=(hoje, fim_semana)
    ).prefetch_related('refeicaoingrediente_set__ingrediente')

    inventario = {
        item.ingrediente_id: item.quantidade
        for item in InventarioItem.objects.filter(household=household)
    }

    necessarios = {}
    for refeicao in refeicoes:
        for ri in refeicao.refeicaoingrediente_set.all():
            ing_id = ri.ingrediente_id
            necessarios[ing_id] = necessarios.get(ing_id, 0) + float(ri.quantidade)

    gerados = 0
    for ing_id, qtd_necessaria in necessarios.items():
        qtd_stock = float(inventario.get(ing_id, 0))
        if qtd_necessaria > qtd_stock:
            try:
                ing = Ingrediente.objects.get(pk=ing_id)
                qtd_a_comprar = qtd_necessaria - qtd_stock
                _, criado = ItemListaCompras.objects.get_or_create(
                    household=household,
                    nome=ing.nome,
                    comprado=False,
                    defaults={
                        'quantidade': f'{qtd_a_comprar:.1f} {ing.unidade}',
                        'gerado_automaticamente': True,
                        'created_by': request.user,
                    }
                )
                if criado:
                    gerados += 1
            except Ingrediente.DoesNotExist:
                pass

    messages.success(request, f'{gerados} itens adicionados automaticamente à lista de compras.')
    return redirect('lista_compras')
