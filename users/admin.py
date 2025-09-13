from django.contrib import admin
from .models import Usuario as User , Rol
# Register your models here.

admin.site.register(User)
admin.site.register(Rol)
