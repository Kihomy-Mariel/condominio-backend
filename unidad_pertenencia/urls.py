from django.urls import path
from . import views

urlpatterns = [
    path('unidades', views.listar_unidades, name='listar_unidades'),
    path('unidades/crear', views.crearUnidad, name='crear_unidad'),
    path('unidades/<int:unidad_id>', views.obtener_unidad, name='obtener_unidad'),
    path('unidades/<int:unidad_id>/editar', views.editar_unidad, name='editar_unidad'),
    path('unidades/<int:unidad_id>/estado',views.cambiar_estado_unidad,name='cambiar_estado_unidad'),
    # URLs para Vehículos
    path('vehiculos', views.listar_vehiculos, name='listar_vehiculos'),
    path('vehiculos/registrar', views.registrar_vehiculo, name='registrar_vehiculo'),
    path('vehiculos/<int:vehiculo_id>', views.obtener_vehiculo, name='obtener_vehiculo'),
    path('vehiculos/<int:vehiculo_id>/editar', views.editar_vehiculo, name='editar_vehiculo'),
    path('vehiculos/<int:vehiculo_id>/estado', views.cambiar_estado_vehiculo, name='cambiar_estado_vehiculo'),
    path('vehiculos/<int:vehiculo_id>/bloquear', views.bloquear_acceso_vehiculo, name='bloquear_acceso_vehiculo'),
    
    # URLs para Mascotas
    path('mascotas', views.listar_mascotas, name='listar_mascotas'),
    path('mascotas/registrar', views.registrar_mascota, name='registrar_mascota'),
    path('mascotas/<int:mascota_id>', views.obtener_mascota, name='obtener_mascota'),
    path('mascotas/<int:mascota_id>/editar', views.editar_mascota, name='editar_mascota'),
    path('mascotas/<int:mascota_id>/estado', views.cambiar_estado_mascota, name='cambiar_estado_mascota'),
]