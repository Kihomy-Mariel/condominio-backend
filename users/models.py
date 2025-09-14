# Create your models here.

from django.contrib.auth.models import AbstractUser
from django.db import models

class Rol(models.Model):
    idRol = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = "rol" 

    def __str__(self):
        return self.name

class Usuario(AbstractUser):
    nombre = models.CharField(max_length=150,blank=True, null=True)
    email = models.EmailField(unique=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    ci = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    ESTADO_CHOICES = (
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    )
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo')
    idRol = models.ForeignKey(Rol, on_delete=models.RESTRICT, db_column="idrol", default=1, blank=True, null=True)  # Relación con Rol, puede ser nulo

    # first_name y last_name ya existen en AbstractUser
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def es_copropietario(self):
        return self.idRol is not None and self.idRol.name == "Copropietario"

    def es_empleado(self):
        return self.idRol is not None and self.idRol.name == "Guardia"

    def es_admin(self):
        return self.idRol is not None and self.idRol.name == "Administrador"

    class Meta:
        db_table = "usuario"

    def __str__(self):
        return self.username


class GuardiaModel(models.Model):
    idUsuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column="id"
    )
    TURNO_CHOICES = (
        ('mañana', 'Mañana'),
        ('tarde', 'Tarde'),
        ('noche', 'Noche'),
    )
    turno = models.CharField(max_length=50, choices=TURNO_CHOICES)
    fecha_contratacion = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'guardia'


class CopropietarioModel(models.Model):
    idUsuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True, db_column="id")
    unidad = models.ForeignKey('unidad_pertenencia.Unidad', on_delete=models.SET_NULL, null=True, blank=True, related_name='copropietarios')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'copropietario'


class PersonaModel(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    documento = models.CharField(max_length=50, unique=True)  # CI
    
    # Relación muchos a muchos: visitante puede visitar a varios copropietarios
    copropietarios = models.ManyToManyField(CopropietarioModel, through="area_comun.AutorizacionVisita")

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    class Meta:
        db_table = 'persona'

class ResidenteModel(models.Model):
    TIPOS=[
        ('copropietario','Copropietario'),
        ('inquilino','Inquilino'),
        ('familiar','Familiar'),
        ('otro','Otro'),
    ]
    # fk de persona
    idPersona = models.ForeignKey(PersonaModel, on_delete=models.CASCADE, related_name='residencias')
    #  fk de copropietario
    idCopropietario = models.ForeignKey(CopropietarioModel, on_delete=models.CASCADE, related_name='residentes')
    tipo = models.CharField(max_length=20, choices=TIPOS, default='copropietario')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email_contacto = models.EmailField(blank=True, null=True)
    class Meta:
        db_table = 'residente'
        constraints = [
            # Impide dos residencias vigentes para el mismo par (copropietario, persona)
            models.UniqueConstraint(
                fields=['idCopropietario', 'idPersona'],
                condition=models.Q(fecha_fin__isnull=True),
                name='uniq_residencia_vigente_por_par',
            ),
            models.CheckConstraint(
            check=(models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gte=models.F('fecha_inicio'))),
            name='chk_residencia_fechas_validas',
        ),
        ]
