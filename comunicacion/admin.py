from django.contrib import admin
from .models import Comunicado

@admin.register(Comunicado)
class ComunicadoAdmin(admin.ModelAdmin):
    list_display = ("id", "titulo", "tipo", "administrador", "fecha_publicacion", "fecha_vencimiento", "activo")
    list_filter = ("tipo", "activo", "fecha_publicacion")
    search_fields = ("titulo", "descripcion", "tipo", "administrador__username")
    ordering = ("-fecha_publicacion", "-id")
