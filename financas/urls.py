from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_despesas, name='lista_despesas'),
    path('nova/', views.criar_despesa, name='criar_despesa'),
    path('<int:pk>/editar/', views.editar_despesa, name='editar_despesa'),
    path('<int:pk>/eliminar/', views.eliminar_despesa, name='eliminar_despesa'),
    path('liquidar/', views.liquidar_saldo, name='liquidar_saldo'),
    path('exportar/', views.exportar_csv, name='exportar_despesas_csv'),
]
