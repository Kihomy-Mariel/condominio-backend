from decimal import Decimal
from django.db import models, transaction
from django.utils import timezone

from users.models import Usuario

from unidad_pertenencia.models import Unidad  

class Tarifa(models.Model):
    nombre = models.CharField(max_length=100, default="Cuota mensual")
    monto_bs = models.DecimalField(max_digits=12, decimal_places=2)
    vigente_desde = models.DateField()
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = "tarifa"
        ordering = ["-vigente_desde"]
    def __str__(self):
        return f"{self.nombre} {self.monto_bs} Bs desde {self.vigente_desde}"

ESTADOS_EXPENSA = (
    ("PENDIENTE", "Pendiente"),
    ("PARCIAL", "Parcial"),
    ("PAGADA", "Pagada"),
    ("ANULADA", "Anulada"),
)

class Expensa(models.Model):
    unidad = models.ForeignKey(Unidad, on_delete=models.PROTECT, related_name="expensas")
    periodo = models.DateField(help_text="Primer día del mes (YYYY-MM-01)")
    vencimiento = models.DateField(null=True, blank=True)
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    saldo = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=10, choices=ESTADOS_EXPENSA, default="PENDIENTE")
    glosa = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = "expensa"
        unique_together = (("unidad", "periodo"),)
        ordering = ["-periodo", "unidad_id"]
    def __str__(self):
        return f"{self.unidad} {self.periodo:%Y-%m} ({self.estado})"
    def recalc_estado(self):
        if self.estado == "ANULADA":
            return
        if self.saldo <= Decimal("0.00"):
            self.estado = "PAGADA"; self.saldo = Decimal("0.00")
        elif self.saldo < self.monto_total:
            self.estado = "PARCIAL"
        else:
            self.estado = "PENDIENTE"

METODOS_PAGO = (
    ("QR", "QR"),
    ("TRANSFERENCIA", "Transferencia"),
    ("EFECTIVO", "Efectivo"),
)

ESTADOS_PAGO = (
    ("PENDIENTE", "Pendiente"),
    ("APROBADO", "Aprobado"),
    ("RECHAZADO", "Rechazado"),
)

def _comprobante_path(instance, filename):
    return f"comprobantes/expensa_{instance.expensa_id}/{filename}"

class Pago(models.Model):
    expensa = models.ForeignKey(Expensa, on_delete=models.CASCADE, related_name="pagos")
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="pagos")
    monto_bs = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_pago = models.DateTimeField(default=timezone.now)
    metodo = models.CharField(max_length=20, choices=METODOS_PAGO, default="TRANSFERENCIA")
    referencia = models.CharField(max_length=120, blank=True, default="")
    comprobante = models.FileField(upload_to=_comprobante_path, null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADOS_PAGO, default="PENDIENTE")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = "pago"
        ordering = ["-created_at"]
    def aplicar_en_expensa(self, signo=+1):
        with transaction.atomic():
            exp = Expensa.objects.select_for_update().get(pk=self.expensa_id)
            if self.estado == "APROBADO":
                exp.saldo = exp.saldo - (self.monto_bs * signo)
                exp.recalc_estado()
                exp.save(update_fields=["saldo", "estado", "updated_at"])
