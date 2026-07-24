from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from decimal import Decimal
import csv
from .models import Despesa, Liquidacao
from .forms import DespesaForm, LiquidacaoForm
from core.views import _calcular_saldo


def household_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.profile.household:
            messages.error(request, 'Precisas de pertencer a um casal primeiro.')
            return redirect('onboarding')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return login_required(wrapper)


@household_required
def lista_despesas(request):
    household = request.user.profile.household
    despesas = Despesa.objects.filter(household=household).select_related(
        'pago_por', 'pago_por__profile', 'created_by', 'created_by__profile'
    )

    mes = request.GET.get('mes')
    ano = request.GET.get('ano')
    categoria = request.GET.get('categoria')
    pago_por = request.GET.get('pago_por')

    hoje = timezone.now().date()
    if not mes:
        mes = str(hoje.month)
    if not ano:
        ano = str(hoje.year)

    despesas = despesas.filter(data__month=mes, data__year=ano)

    if categoria:
        despesas = despesas.filter(categoria=categoria)
    if pago_por:
        despesas = despesas.filter(pago_por__id=pago_por)

    total = sum(d.valor for d in despesas)
    por_categoria = {}
    for d in despesas:
        cat = d.get_categoria_display()
        por_categoria[cat] = por_categoria.get(cat, Decimal('0')) + d.valor

    parceiro = household.parceiro(request.user)
    saldo = _calcular_saldo(household, request.user, parceiro)

    from .models import CATEGORIAS
    ctx = {
        'despesas': despesas,
        'total': total,
        'por_categoria': por_categoria,
        'saldo': saldo,
        'parceiro': parceiro,
        'household': household,
        'mes_atual': mes,
        'ano_atual': ano,
        'categorias': CATEGORIAS,
        'membros': household.membros(),
        'filtro_categoria': categoria,
        'filtro_pago_por': pago_por,
    }
    return render(request, 'financas/lista.html', ctx)


@household_required
def criar_despesa(request):
    household = request.user.profile.household
    if request.method == 'POST':
        form = DespesaForm(request.POST, household=household, user=request.user)
        if form.is_valid():
            despesa = form.save(commit=False)
            despesa.household = household
            despesa.created_by = request.user
            despesa.save()
            messages.success(request, 'Despesa adicionada.')
            return redirect('lista_despesas')
    else:
        from django.utils import timezone
        form = DespesaForm(
            household=household,
            user=request.user,
            initial={'data': timezone.now().date(), 'pago_por': request.user}
        )
    return render(request, 'financas/form_despesa.html', {'form': form, 'titulo': 'Nova Despesa'})


@household_required
def editar_despesa(request, pk):
    household = request.user.profile.household
    despesa = get_object_or_404(Despesa, pk=pk, household=household)
    if request.method == 'POST':
        form = DespesaForm(request.POST, instance=despesa, household=household, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Despesa atualizada.')
            return redirect('lista_despesas')
    else:
        form = DespesaForm(instance=despesa, household=household, user=request.user)
    return render(request, 'financas/form_despesa.html', {'form': form, 'titulo': 'Editar Despesa', 'despesa': despesa})


@household_required
def eliminar_despesa(request, pk):
    household = request.user.profile.household
    despesa = get_object_or_404(Despesa, pk=pk, household=household)
    if request.method == 'POST':
        despesa.delete()
        messages.success(request, 'Despesa eliminada.')
        return redirect('lista_despesas')
    return render(request, 'financas/confirmar_eliminar.html', {'objeto': despesa, 'tipo': 'despesa'})


@household_required
def liquidar_saldo(request):
    household = request.user.profile.household
    parceiro = household.parceiro(request.user)
    saldo = _calcular_saldo(household, request.user, parceiro)

    if not saldo['deve'] or saldo['valor'] == 0:
        messages.info(request, 'Não há saldo a liquidar.')
        return redirect('lista_despesas')

    if request.method == 'POST':
        form = LiquidacaoForm(request.POST)
        if form.is_valid():
            liq = form.save(commit=False)
            liq.household = household
            liq.de = request.user
            liq.para = parceiro
            liq.save()
            messages.success(request, f'Liquidação de {liq.valor} {household.simbolo_moeda()} registada.')
            return redirect('lista_despesas')
    else:
        form = LiquidacaoForm(initial={'valor': saldo['valor']})

    return render(request, 'financas/liquidar.html', {
        'form': form, 'saldo': saldo, 'parceiro': parceiro, 'household': household
    })


@household_required
def exportar_csv(request):
    household = request.user.profile.household
    mes = request.GET.get('mes', timezone.now().month)
    ano = request.GET.get('ano', timezone.now().year)

    despesas = Despesa.objects.filter(
        household=household, data__month=mes, data__year=ano
    ).select_related('pago_por', 'created_by').order_by('data')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="despesas_{ano}_{mes:02}.csv"'
    response.write('﻿')

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Data', 'Descrição', 'Categoria', 'Valor', 'Pago por', 'Divisão', 'Valor A', 'Valor B', 'Notas'])
    for d in despesas:
        writer.writerow([
            d.data, d.descricao, d.get_categoria_display(),
            d.valor, d.pago_por.get_full_name() or d.pago_por.username,
            d.get_divisao_display(), d.valor_pessoa_a, d.valor_pessoa_b, d.notas
        ])

    return response
