from django.db import models

# IMPORTAR USUARIO DESDE USERS
from users.models import Usuario
# Create your models here.
class Comunicado(models.Model):
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    imagen_url = models.URLField(null=True, blank=True)
    fecha_publicacion = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    tipo = models.CharField(max_length=50)  # ANUNCIO,COMUNICADO,ADVERTENCIA,ETC
    administrador =  models.ForeignKey(
    Usuario, 
    on_delete=models.CASCADE, 
    db_column='administrador_id',
    )# ID del administrador que crea el comunicado
    activo = models.BooleanField(default=True)

    # def __str__(self):
    #     return f"{self.titulo} ({self.tipo})"

    class Meta:
        db_table = 'comunicado'
