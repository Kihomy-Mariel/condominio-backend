from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AreaComunViewSet, ReservaViewSet, mostrarVisitas, marcarEntradaVisita, marcarSalidaVisita

router = DefaultRouter()
router.register(r'areas', AreaComunViewSet, basename='areas')
router.register(r'reservas', ReservaViewSet, basename='reservas')

urlpatterns = [
    # Visitas (guardia)
    path('mostrarVisitas', mostrarVisitas, name='mostrarVisitas'),
    path('marcarEntrada', marcarEntradaVisita, name='marcarEntrada'),
    path('marcarSalida', marcarSalidaVisita, name='marcarSalida'),

    # Router
    path('', include(router.urls)),
]
