from django.db import models


# Create your models here.
class Unidad(models.Model):
    # Opciones para tipo_unidad
    TIPOS_UNIDAD = [
        ("apartamento", "Apartamento"),
        ("casa", "Casa"),
        ("local", "Local Comercial"),
        ("oficina", "Oficina"),
        ("deposito", "Depósito"),
        ("parqueadero", "Parqueadero"),
        ("otro", "Otro"),
    ]
    codigo = models.CharField(max_length=20, unique=True)
    bloque = models.CharField(max_length=10)
    piso = models.IntegerField()
    numero = models.CharField(max_length=10)
    area_m2 = models.DecimalField(max_digits=8, decimal_places=2)
    estado = models.CharField(max_length=20, default="activa")
    tipo_unidad = models.CharField(
        max_length=20,
        choices=TIPOS_UNIDAD,
        default="apartamento",
        help_text="Tipo de unidad",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "unidad"

    def __str__(self):
        return f"Unidad {self.codigo} - Bloque {self.bloque}, Piso {self.piso}, Numero {self.numero}"


class Pertenencia(models.Model):
    # CLASE BASE ABSTRACTA - Implementa la generalización
    unidad = models.ForeignKey(
        Unidad,
        on_delete=models.CASCADE,
        related_name="%(class)ss",  # → 'vehiculos' para Vehiculo, 'mascotas' para Mascota
        related_query_name="%(class)s",
    )
    activo = models.BooleanField(default=True)
    acceso_bloqueado = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True  # clase abstracta, no se crea tabla


class Vehiculo(Pertenencia):
    ESTADOS_VEHICULO = [
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
        ("bloqueado", "Bloqueado"),
    ]

    TIPOS_VEHICULO = [
        ("automovil", "Automóvil"),
        ("motocicleta", "Motocicleta"),
        ("camioneta", "Camioneta"),
        ("bicicleta", "Bicicleta"),
        ("otro", "Otro"),
    ]
    placa = models.CharField(max_length=10, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    color = models.CharField(max_length=30, blank=True)
    tag_codigo = models.CharField(
        max_length=50, unique=True, help_text="Código unico del tag de acceso"
    )
    estado = models.CharField(max_length=20, choices=ESTADOS_VEHICULO, default="activo")
    tipo_vehiculo = models.CharField(
        max_length=20, choices=TIPOS_VEHICULO, default="automovil"
    )

    class Meta:
        db_table = "vehiculo"

    def __str__(self):
        return f"Vehiculo {self.placa} - {self.marca} {self.modelo} ({self.color})"


class Mascota(Pertenencia):
    TIPOS_MASCOTA = [
        ("perro", "Perro"),
        ("gato", "Gato"),
        ("ave", "Ave"),
        ("pez", "Pez"),
        ("otro", "Otro"),
    ]
    nombre = models.CharField(max_length=50)
    tipo_mascota = models.CharField(
        max_length=20, choices=TIPOS_MASCOTA, default="otro"
    )
    raza = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=30, null=True, blank=True)
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "mascota"

    def __str__(self):
        return f"Mascota {self.nombre} - {self.tipo_mascota} ({self.color})"
