from django.urls import path
from . import views

urlpatterns = [
    path('crearComunicado/<int:administrador_id>', views.crearComunicado, name='crearComunicado'),
    path('mostrarComunicados', views.ListarComunicado, name="mostrarComunicados"),
]