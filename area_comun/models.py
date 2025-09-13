from django.db import models
from django.utils import timezone
from users.models import CopropietarioModel, PersonaModel, GuardiaModel
from users.models import Usuario as User



# LO QUE TENIA PARA CALENDARIO DE AREAS COMUNES

class AreaComun(models.Model):
    id_area = models.AutoField(primary_key=True)
    nombre_area = models.CharField(max_length=100, unique=True)
    capacidad = models.PositiveIntegerField()
    requiere_pago = models.BooleanField(default=False)
    precio_por_bloque = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    apertura_hora = models.TimeField()
    cierre_hora = models.TimeField()
    dias_habiles = models.CharField(max_length=50) # Ej: Lunes a Viernes, luego cambiar por tabla horarios
    reglas = models.TextField(blank=True)     
    ESTADO_CHOICES = (
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('ocupado', 'Ocupado'),
        ('libre', 'Libre'),
    )
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo') # luego cambiar estados

    class Meta:
        db_table = 'area_comun'
    def _str_(self):
        return self.nombre_area


class Reserva(models.Model):
    id_reserva = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(CopropietarioModel, on_delete=models.CASCADE, related_name="reservas")
    area_comun = models.ForeignKey(AreaComun, on_delete=models.CASCADE, related_name="reservas")
    
    fecha = models.DateField(null=True, blank=True)
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)
    url_comprobante = models.URLField(null=True, blank=True)

    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    )
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    
    nota = models.TextField(blank=True)
    creada_en = models.DateTimeField(default=timezone.now)
    cancelada_en = models.DateTimeField(null=True, blank=True)
    motivo_cancelacion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'reserva'
    def __str__(self):
        return f"{self.area_comun.nombre_area} - {self.usuario.usuario.username} ({self.fecha})"




class AutorizacionVisita(models.Model):
    visitante = models.ForeignKey(PersonaModel, on_delete=models.CASCADE)
    copropietario = models.ForeignKey(CopropietarioModel, on_delete=models.CASCADE)
    hora_inicio = models.DateTimeField()
    hora_fin = models.DateTimeField()
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('en visita', 'En Visita'),
        ('completada', 'Completada'),
    )
    estado = models.CharField(max_length=20, default="Pendiente")
    motivo_visita = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.visitante} autorizado por {self.copropietario} de {self.hora_inicio} a {self.hora_fin}"

    class Meta:
        db_table = 'autorizacion_visita'



# LO QUE TENIA EN GUARDIA

class RegistroVisitaModel(models.Model):
    autorizacion = models.ForeignKey(AutorizacionVisita, on_delete=models.CASCADE)
    guardia = models.ForeignKey(GuardiaModel, on_delete=models.CASCADE)
    fecha_entrada = models.DateTimeField(auto_now_add=True, null=True)
    fecha_salida = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Visita de {self.autorizacion.visitante} a {self.autorizacion.copropietario} registrada por {self.guardia}"

    class Meta:
        db_table = 'registro_visita'
