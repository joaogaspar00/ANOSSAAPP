from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_tarefas, name='lista_tarefas'),
    path('nova/', views.criar_tarefa, name='criar_tarefa'),
    path('<int:pk>/editar/', views.editar_tarefa, name='editar_tarefa'),
    path('<int:pk>/eliminar/', views.eliminar_tarefa, name='eliminar_tarefa'),
    path('<int:pk>/concluir/', views.concluir_tarefa, name='concluir_tarefa'),
    path('<int:pk>/mover/', views.mover_estado, name='mover_estado_tarefa'),
]
