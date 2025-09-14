from django.db import models
from django.utils import timezone
from django.db.models import Q
from django.contrib.postgres.fields import DateTimeRangeField
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields.ranges import RangeOperators

from users.models import CopropietarioModel, PersonaModel, GuardiaModel
from users.models import Usuario as User

# ================== ÁREAS COMUNES ==================

class AreaComun(models.Model):
    id_area = models.AutoField(primary_key=True)
    nombre_area = models.CharField(max_length=100, unique=True)
    capacidad = models.PositiveIntegerField()
    requiere_pago = models.BooleanField(default=False)
    precio_por_bloque = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Operativa
    apertura_hora = models.TimeField()
    cierre_hora = models.TimeField()
    bloque_minutos = models.PositiveIntegerField(default=60, help_text="Tamaño del bloque en minutos (p.ej. 60).")
    antelacion_min_horas = models.PositiveIntegerField(default=24, help_text="Reserva con al menos X horas de anticipación.")
    max_dias_adelante = models.PositiveIntegerField(default=30, help_text="Máximo de días hacia adelante.")
    # Días hábiles como CSV de números 0-6 (0=lunes ... 6=domingo) => '0,1,2,3,4,5'
    dias_habiles = models.CharField(max_length=20, default="0,1,2,3,4,5", help_text="CSV de días 0-6, 0=lun...6=dom")

    ESTADO_CHOICES = (
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    )
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo')

    class Meta:
        db_table = 'area_comun'

    def __str__(self):
        return self.nombre_area

    def dia_habil(self, fecha):
        # 0=lunes ... 6=domingo (Python: Monday=0)
        try:
            permitidos = {int(x) for x in self.dias_habiles.split(",") if x.strip() != ""}
        except Exception:
            permitidos = {0,1,2,3,4,5}
        return fecha.weekday() in permitidos


# ================== RESERVAS ==================

class Reserva(models.Model):
    id_reserva = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(CopropietarioModel, on_delete=models.CASCADE, related_name="reservas")
    area_comun = models.ForeignKey(AreaComun, on_delete=models.CASCADE, related_name="reservas")

    fecha = models.DateField(null=True, blank=True)
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)

    # ➜ NUEVOS (ponlos así, con null=True/blank=True)
    inicio = models.DateTimeField(null=True, blank=True)
    fin = models.DateTimeField(null=True, blank=True)

    intervalo = DateTimeRangeField(null=True, blank=True)
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
        constraints = [
            models.CheckConstraint(
                check=Q(fin__gt=models.F('inicio')),
                name='chk_reserva_fin_gt_inicio'
            ),
            # Prohíbe solapamientos por área cuando estado != cancelada
            ExclusionConstraint(
                name='exc_reserva_no_overlap_por_area',
                expressions=[
                    ('area_comun', RangeOperators.EQUAL),
                    ('intervalo', RangeOperators.OVERLAPS),
                ],
                condition=Q(estado__in=['pendiente', 'confirmada']),
            ),
        ]
        indexes = [
            models.Index(fields=['area_comun', 'inicio']),
            models.Index(fields=['area_comun', 'fin']),
        ]

    def __str__(self):
        try:
            return f"{self.area_comun.nombre_area} - {self.usuario.idUsuario.username} ({self.fecha})"
        except Exception:
            return f"Reserva {self.pk}"
        
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
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    motivo_visita = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'autorizacion_visita'

    def __str__(self):
        return f"{self.visitante} autorizado por {self.copropietario} de {self.hora_inicio} a {self.hora_fin}"

class RegistroVisitaModel(models.Model):
    autorizacion = models.ForeignKey(AutorizacionVisita, on_delete=models.CASCADE)
    guardia = models.ForeignKey(GuardiaModel, on_delete=models.CASCADE)
    fecha_entrada = models.DateTimeField(auto_now_add=True, null=True)
    fecha_salida = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'registro_visita'

    def __str__(self):
        return f"Visita de {self.autorizacion.visitante} registrada por {self.guardia}"