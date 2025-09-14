from django.db import models
from users.models import Usuario

class Comunicado(models.Model):
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    imagen_url = models.URLField(null=True, blank=True)
    fecha_publicacion = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    tipo = models.CharField(max_length=50)  # ANUNCIO, COMUNICADO, ADVERTENCIA, etc.
    administrador = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column="administrador_id",
        related_name="comunicados"
    )
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "comunicado"
        ordering = ["-fecha_publicacion", "-id"]

    def __str__(self):
        return f"{self.titulo} ({self.tipo})"
