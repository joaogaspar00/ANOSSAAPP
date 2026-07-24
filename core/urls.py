from django.urls import path
from . import views

urlpatterns = [
    path('', views.pagina_inicial, name='pagina_inicial'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('entrar/', views.login_view, name='login'),
    path('sair/', views.logout_view, name='logout'),
    path('registar/', views.registo, name='registo'),
    path('onboarding/', views.onboarding, name='onboarding'),
    path('convite/<uuid:token>/', views.aceitar_convite, name='aceitar_convite'),
    path('perfil/', views.perfil, name='perfil'),
    path('definicoes/', views.definicoes_household, name='definicoes_household'),
]
