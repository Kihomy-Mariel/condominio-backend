from django.contrib import admin
from .models import Tarifa, Expensa, Pago

@admin.register(Tarifa)
class TarifaAdmin(admin.ModelAdmin):
    list_display = ("id","nombre","monto_bs","vigente_desde","activa")
    list_filter = ("activa",)

@admin.register(Expensa)
class ExpensaAdmin(admin.ModelAdmin):
    list_display = ("id","unidad","periodo","monto_total","saldo","estado")
    list_filter = ("estado","periodo")
    search_fields = ("unidad__codigo",)

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("id","expensa","usuario","monto_bs","estado","created_at")
    list_filter = ("estado","metodo")
    actions = ["aprobar_pagos","rechazar_pagos"]
    def aprobar_pagos(self, request, queryset):
        n=0
        for p in queryset:
            if p.estado != "APROBADO":
                p.estado = "APROBADO"; p.save(update_fields=["estado"]); n+=1
        self.message_user(request, f"{n} pagos aprobados.")
    def rechazar_pagos(self, request, queryset):
        n=0
        for p in queryset:
            if p.estado != "RECHAZADO":
                p.estado = "RECHAZADO"; p.save(update_fields=["estado"]); n+=1
        self.message_user(request, f"{n} pagos rechazados.")
