from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_objetivos, name='lista_objetivos'),
    path('novo/', views.criar_objetivo, name='criar_objetivo'),
    path('<int:pk>/editar/', views.editar_objetivo, name='editar_objetivo'),
    path('<int:pk>/eliminar/', views.eliminar_objetivo, name='eliminar_objetivo'),
    path('<int:pk>/progresso/', views.atualizar_progresso, name='atualizar_progresso'),
]
