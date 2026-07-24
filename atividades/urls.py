from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_atividades, name='lista_atividades'),
    path('nova/', views.criar_atividade, name='criar_atividade'),
    path('<int:pk>/editar/', views.editar_atividade, name='editar_atividade'),
    path('<int:pk>/eliminar/', views.eliminar_atividade, name='eliminar_atividade'),
    path('<int:pk>/avaliar/', views.avaliar_atividade, name='avaliar_atividade'),
    path('<int:pk>/mover/', views.mover_estado_atividade, name='mover_estado_atividade'),
]
