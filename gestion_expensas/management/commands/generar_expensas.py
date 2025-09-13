from calendar import monthrange
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction

from unidad_pertenencia.models import Unidad  
from gestion_expensas.models import Expensa, Tarifa

class Command(BaseCommand):
    help = "Genera expensas para todas las unidades ACTIVAS del periodo YYYY-MM (usa día 01)."
    def add_arguments(self, parser):
        parser.add_argument("--periodo", help="YYYY-MM", required=False)
    def handle(self, *args, **opts):
        hoy = date.today()
        if opts["periodo"]:
            y, m = opts["periodo"].split("-")
            periodo = date(int(y), int(m), 1)
        else:
            periodo = date(hoy.year, hoy.month, 1)

        tarifa = Tarifa.objects.filter(activa=True, vigente_desde__lte=periodo).order_by("-vigente_desde").first()
        if not tarifa:
            self.stderr.write("No hay Tarifa activa."); return

        _, last = monthrange(periodo.year, periodo.month)
        venc = date(periodo.year, periodo.month, last)

        creadas = 0
        with transaction.atomic():
            for u in Unidad.objects.filter(estado="activa"):  # 🔎 tu modelo usa string 'activa'
                _, created = Expensa.objects.get_or_create(
                    unidad=u, periodo=periodo,
                    defaults=dict(
                        vencimiento=venc,
                        monto_total=tarifa.monto_bs,
                        saldo=tarifa.monto_bs,
                        glosa=f"Expensa {periodo:%Y-%m} según {tarifa.nombre}",
                    ),
                )
                if created: creadas += 1
        self.stdout.write(self.style.SUCCESS(f"Periodo {periodo:%Y-%m}: {creadas} expensas creadas."))
