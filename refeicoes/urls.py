from django.urls import path
from . import views

urlpatterns = [
    path('', views.planeamento, name='planeamento'),
    path('nova/', views.criar_refeicao, name='criar_refeicao'),
    path('<int:pk>/editar/', views.editar_refeicao, name='editar_refeicao'),
    path('<int:pk>/eliminar/', views.eliminar_refeicao, name='eliminar_refeicao'),
    path('compras/', views.lista_compras, name='lista_compras'),
    path('compras/<int:pk>/comprado/', views.marcar_comprado, name='marcar_comprado'),
    path('compras/<int:pk>/eliminar/', views.eliminar_item_compras, name='eliminar_item_compras'),
    path('compras/limpar/', views.limpar_comprados, name='limpar_comprados'),
    path('compras/gerar/', views.gerar_lista_compras, name='gerar_lista_compras'),
    path('inventario/', views.inventario, name='inventario'),
]
