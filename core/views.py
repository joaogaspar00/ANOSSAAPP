from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Household, UserProfile
from .forms import RegistoForm, LoginForm, HouseholdForm, PerfilForm


def pagina_inicial(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


def registo(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    token_convite = request.GET.get('convite') or request.session.get('token_convite')
    household_convite = None

    if token_convite:
        try:
            household_convite = Household.objects.get(token_convite=token_convite, convite_ativo=True)
            if household_convite.esta_completo():
                messages.error(request, 'Este convite já não está disponível.')
                household_convite = None
            else:
                request.session['token_convite'] = str(token_convite)
        except Household.DoesNotExist:
            messages.error(request, 'Convite inválido ou expirado.')

    if request.method == 'POST':
        form = RegistoForm(request.POST)
        if form.is_valid():
            user = form.save()
            token = request.session.get('token_convite')
            if token:
                try:
                    hh = Household.objects.get(token_convite=token, convite_ativo=True)
                    if not hh.esta_completo():
                        user.profile.household = hh
                        user.profile.save()
                        if hh.esta_completo():
                            hh.convite_ativo = False
                            hh.save()
                        del request.session['token_convite']
                        login(request, user)
                        messages.success(request, f'Bem-vindo ao casal {hh.nome}!')
                        return redirect('dashboard')
                except Household.DoesNotExist:
                    pass
            login(request, user)
            messages.success(request, 'Conta criada! Configura o teu casal.')
            return redirect('onboarding')
    else:
        form = RegistoForm()

    return render(request, 'core/registo.html', {'form': form, 'household_convite': household_convite})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Utilizador ou palavra-passe incorretos.')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def onboarding(request):
    if request.user.profile.household:
        return redirect('dashboard')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'criar':
            form = HouseholdForm(request.POST)
            if form.is_valid():
                hh = form.save()
                request.user.profile.household = hh
                request.user.profile.save()
                messages.success(request, f'Casal "{hh.nome}" criado! Partilha o convite com o teu parceiro.')
                return redirect('dashboard')
        else:
            form = HouseholdForm()
    else:
        form = HouseholdForm()
    return render(request, 'core/onboarding.html', {'form': form})


def aceitar_convite(request, token):
    household = get_object_or_404(Household, token_convite=token, convite_ativo=True)
    if household.esta_completo():
        messages.error(request, 'Este convite já não está disponível — o casal está completo.')
        return redirect('login')

    if request.user.is_authenticated:
        if request.user.profile.household:
            messages.warning(request, 'Já pertences a um casal.')
            return redirect('dashboard')
        request.user.profile.household = household
        request.user.profile.save()
        if household.esta_completo():
            household.convite_ativo = False
            household.save()
        messages.success(request, f'Juntaste-te ao casal {household.nome}!')
        return redirect('dashboard')

    request.session['token_convite'] = str(token)
    messages.info(request, f'Regista-te para te juntares ao casal "{household.nome}".')
    return redirect('registo')


@login_required
def dashboard(request):
    profile = request.user.profile
    household = profile.household

    if not household:
        return redirect('onboarding')

    hoje = timezone.now().date()
    amanha = hoje + timedelta(days=1)
    proxima_semana = hoje + timedelta(days=7)
    parceiro = household.parceiro(request.user)

    from tarefas.models import Tarefa
    from financas.models import Despesa
    from refeicoes.models import Refeicao
    from calendario.models import EventoCalendario

    tarefas_pendentes = Tarefa.objects.filter(
        household=household, estado__in=['pendente', 'em_curso']
    ).select_related('atribuida_a', 'atribuida_a__profile').order_by('data_limite')[:5]

    eventos_proximos = EventoCalendario.objects.filter(
        household=household,
        data_inicio__date__gte=hoje,
        data_inicio__date__lte=proxima_semana,
    ).filter(visibilidade='partilhado').order_by('data_inicio')[:5]

    refeicoes_hoje = Refeicao.objects.filter(household=household, data=hoje)
    refeicoes_amanha = Refeicao.objects.filter(household=household, data=amanha)

    despesas_recentes = Despesa.objects.filter(household=household).select_related(
        'pago_por', 'pago_por__profile'
    )[:5]

    saldo = _calcular_saldo(household, request.user, parceiro)

    ultimas_atividades_parceiro = []
    if parceiro:
        from atividades.models import Atividade
        ultimas_atividades_parceiro = Atividade.objects.filter(
            household=household, created_by=parceiro
        )[:3]

    ctx = {
        'household': household,
        'parceiro': parceiro,
        'tarefas_pendentes': tarefas_pendentes,
        'eventos_proximos': eventos_proximos,
        'refeicoes_hoje': refeicoes_hoje,
        'refeicoes_amanha': refeicoes_amanha,
        'despesas_recentes': despesas_recentes,
        'saldo': saldo,
        'ultimas_atividades_parceiro': ultimas_atividades_parceiro,
        'hoje': hoje,
    }
    return render(request, 'dashboard.html', ctx)


def _calcular_saldo(household, user, parceiro):
    if not parceiro:
        return {'deve': None, 'valor': 0}

    from financas.models import Despesa, Liquidacao
    from decimal import Decimal

    membros = list(household.membros())
    if len(membros) < 2:
        return {'deve': None, 'valor': 0}

    user_a = membros[0]
    user_b = membros[1]

    total_a_deve_a_b = Decimal('0')
    total_b_deve_a_a = Decimal('0')

    for despesa in Despesa.objects.filter(household=household):
        if despesa.pago_por == user_b:
            total_a_deve_a_b += despesa.valor_pessoa_a
        elif despesa.pago_por == user_a:
            total_b_deve_a_a += despesa.valor_pessoa_b

    for liq in Liquidacao.objects.filter(household=household):
        if liq.de == user_a and liq.para == user_b:
            total_a_deve_a_b -= liq.valor
        elif liq.de == user_b and liq.para == user_a:
            total_b_deve_a_a -= liq.valor

    saldo_liquido = total_a_deve_a_b - total_b_deve_a_a

    if user == user_a:
        if saldo_liquido > 0:
            return {'deve': True, 'valor': abs(saldo_liquido), 'a_quem': parceiro}
        elif saldo_liquido < 0:
            return {'deve': False, 'valor': abs(saldo_liquido), 'a_quem': user}
    else:
        if saldo_liquido < 0:
            return {'deve': True, 'valor': abs(saldo_liquido), 'a_quem': parceiro}
        elif saldo_liquido > 0:
            return {'deve': False, 'valor': abs(saldo_liquido), 'a_quem': user}

    return {'deve': None, 'valor': 0}


@login_required
def perfil(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            form.save_user_data(request.user)
            messages.success(request, 'Perfil atualizado.')
            return redirect('perfil')
    else:
        form = PerfilForm(instance=profile, user=request.user)
    return render(request, 'core/perfil.html', {'form': form})


@login_required
def definicoes_household(request):
    household = request.user.profile.household
    if not household:
        return redirect('onboarding')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'guardar':
            form = HouseholdForm(request.POST, instance=household)
            if form.is_valid():
                form.save()
                messages.success(request, 'Definições do casal atualizadas.')
                return redirect('definicoes_household')
        elif action == 'novo_convite':
            import uuid
            household.token_convite = uuid.uuid4()
            household.convite_ativo = True
            household.save()
            messages.success(request, 'Novo link de convite gerado.')
            return redirect('definicoes_household')
        elif action == 'desativar_convite':
            household.convite_ativo = False
            household.save()
            messages.info(request, 'Convite desativado.')
            return redirect('definicoes_household')
        form = HouseholdForm(instance=household)
    else:
        form = HouseholdForm(instance=household)

    convite_url = request.build_absolute_uri(f'/convite/{household.token_convite}/')
    return render(request, 'core/definicoes_household.html', {
        'form': form,
        'household': household,
        'convite_url': convite_url,
    })
