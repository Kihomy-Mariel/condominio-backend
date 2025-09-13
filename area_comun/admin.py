from django.contrib import admin

# Register your models here.
from .models import AreaComun, Reserva

admin.site.register(AreaComun)
admin.site.register(Reserva)
