from django.contrib import admin

try:
    from .models import AreaComun, Reserva, AutorizacionVisita, RegistroVisitaModel
    HAS_VISITAS = True
except Exception:
    from .models import AreaComun, Reserva
    AutorizacionVisita = RegistroVisitaModel = None
    HAS_VISITAS = False

@admin.register(AreaComun)
class AreaComunAdmin(admin.ModelAdmin):
    list_display = ("id_area","nombre_area","capacidad","estado")
    list_filter = ("estado",)

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ("id_reserva","area_comun","usuario","fecha","hora_inicio","hora_fin","estado")
    list_filter = ("estado","area_comun","fecha")

if HAS_VISITAS and AutorizacionVisita:
    @admin.register(AutorizacionVisita)
    class AutorizacionVisitaAdmin(admin.ModelAdmin):
        list_display = ("id","visitante","copropietario","hora_inicio","hora_fin","estado")
        list_filter = ("estado",)

if HAS_VISITAS and RegistroVisitaModel:
    @admin.register(RegistroVisitaModel)
    class RegistroVisitaAdmin(admin.ModelAdmin):
        list_display = ("id","autorizacion","guardia","fecha_entrada","fecha_salida")
