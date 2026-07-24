from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendario_mensal, name='calendario'),
    path('eventos/', views.lista_eventos, name='lista_eventos'),
    path('novo/', views.criar_evento, name='criar_evento'),
    path('<int:pk>/editar/', views.editar_evento, name='editar_evento'),
    path('<int:pk>/eliminar/', views.eliminar_evento, name='eliminar_evento'),
]
