from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
from .views import AreaComunViewSet, ReservaViewSet

# 1. Configuración del router de DRF
router = DefaultRouter()
router.register(r'areas', AreaComunViewSet, basename='areas')
router.register(r'reservas', ReservaViewSet, basename='reservas')

# 2. Rutas tradicionales
urlpatterns = [
    path('marcarEntrada', views.marcarEntradaVisita, name='marcarEntrada'),
    path('marcarSalida', views.marcarSalidaVisita, name='marcarSalida'),
    path('mostrarCalendarioAreasComunes', views.mostrarCalendarioAreasComunes, name='mostrarCalendarioAreasComunes'),
    # path('crearListaInvitados<int:copropietario_id>', views.crearListaInvitados, name='crearListaInvitados'),
    #LISTAR VISITAS PARA EL GUARDIA
    path('mostrarVisitas', views.mostrarVisitas, name='mostrarVisitas'),
]

# 3. Agregar las del router a urlpatterns
urlpatterns += router.urls
