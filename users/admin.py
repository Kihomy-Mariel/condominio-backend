from django.contrib import admin
from .models import Usuario as User, Rol, GuardiaModel, CopropietarioModel, PersonaModel, ResidenteModel
admin.site.register(User)
admin.site.register(Rol)
admin.site.register(GuardiaModel)
admin.site.register(CopropietarioModel)
admin.site.register(PersonaModel)
admin.site.register(ResidenteModel)
