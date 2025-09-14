# unidad_pertenencia/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UnidadViewSet, VehiculoViewSet, MascotaViewSet

router = DefaultRouter()
router.register(r'unidades', UnidadViewSet, basename='unidades')
router.register(r'vehiculos', VehiculoViewSet, basename='vehiculos')
router.register(r'mascotas', MascotaViewSet, basename='mascotas')

urlpatterns = [
    path('', include(router.urls)),
]
