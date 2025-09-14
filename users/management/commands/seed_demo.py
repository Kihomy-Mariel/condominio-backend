# gestion_expensas/management/commands/seed_demo.py
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from django.utils import timezone
from decimal import Decimal
from datetime import date, time, datetime, timedelta
from calendar import monthrange

from users.models import Rol, Usuario, CopropietarioModel
from unidad_pertenencia.models import Unidad
from area_comun.models import AreaComun, Reserva
from gestion_expensas.models import Tarifa, Expensa


class Command(BaseCommand):
    help = "Carga datos de demo: unidades, áreas, copropietario, tarifa, expensas y una reserva."

    @transaction.atomic
    def handle(self, *args, **opts):
        # 1) Roles mínimos
        for r in ["Administrador", "Guardia", "Empleado", "Copropietario"]:
            Rol.objects.get_or_create(name=r)

        # 2) Unidades
        u1, _ = Unidad.objects.get_or_create(
            codigo="A-101",
            defaults=dict(
                bloque="A", piso=1, numero="101",
                area_m2=Decimal("85.50"),
                estado="activa", tipo_unidad="apartamento"
            )
        )
        u2, _ = Unidad.objects.get_or_create(
            codigo="A-102",
            defaults=dict(
                bloque="A", piso=1, numero="102",
                area_m2=Decimal("78.00"),
                estado="activa", tipo_unidad="apartamento"
            )
        )

        # 3) Copropietario demo (A-101)
        rol_copro = Rol.objects.get(name="Copropietario")
        user_copro, created = Usuario.objects.get_or_create(
            username="user_a101",
            defaults=dict(
                email="user_a101@example.com",
                nombre="Titular A101",
                ci="C-A101",
                telefono="70010001",
                idRol=rol_copro,
            )
        )
        if created:
            user_copro.set_password("Clave123")
            user_copro.save()

        cp, _ = CopropietarioModel.objects.get_or_create(idUsuario=user_copro)
        # Soporta tanto CharField como FK para 'unidad'
        if hasattr(cp, "unidad_id"):  # FK a Unidad
            cp.unidad = u1
        else:  # CharField
            cp.unidad = u1.codigo
        cp.save()

        # 4) Áreas comunes
        salon, _ = AreaComun.objects.get_or_create(
            nombre_area="Salón de Eventos",
            defaults=dict(
                capacidad=50,
                requiere_pago=False,
                precio_por_bloque=Decimal("0.00"),
                apertura_hora=time(8, 0),
                cierre_hora=time(22, 0),
                dias_habiles="0,1,2,3,4,5,6",
                estado="activo",
            )
        )
        churras, _ = AreaComun.objects.get_or_create(
            nombre_area="Churrasquera",
            defaults=dict(
                capacidad=20,
                requiere_pago=False,
                precio_por_bloque=Decimal("0.00"),
                apertura_hora=time(9, 0),
                cierre_hora=time(21, 0),
                dias_habiles="0,1,2,3,4,5,6",
                estado="activo",
            )
        )

        # 5) Tarifa vigente y expensas del mes actual
        hoy = timezone.localdate()
        periodo = date(hoy.year, hoy.month, 1)
        Tarifa.objects.get_or_create(
            nombre="Cuota mensual",
            vigente_desde=periodo,
            defaults=dict(monto_bs=Decimal("300.00"), activa=True),
        )

        tarifa = (
            Tarifa.objects
            .filter(activa=True, vigente_desde__lte=periodo)
            .order_by("-vigente_desde")
            .first()
        )
        if not tarifa:
            raise RuntimeError("No hay tarifa activa.")

        venc = date(periodo.year, periodo.month, monthrange(periodo.year, periodo.month)[1])

        creadas = 0
        for u in Unidad.objects.filter(estado="activa"):
            _, created = Expensa.objects.get_or_create(
                unidad=u, periodo=periodo,
                defaults=dict(
                    vencimiento=venc,
                    monto_total=tarifa.monto_bs,
                    saldo=tarifa.monto_bs,
                    estado="PENDIENTE",
                    glosa=f"{tarifa.nombre} {periodo:%Y-%m}",
                )
            )
            if created:
                creadas += 1

        # 6) Reserva demo para mañana 10:00-12:00 (anti-solape por constraint)
        maniana = hoy + timedelta(days=1)
        tz = timezone.get_current_timezone()
        inicio = timezone.make_aware(datetime.combine(maniana, time(10, 0)), tz)
        fin = timezone.make_aware(datetime.combine(maniana, time(12, 0)), tz)
        try:
            Reserva.objects.get_or_create(
                usuario=cp,
                area_comun=salon,
                fecha=maniana,
                hora_inicio=time(10, 0),
                hora_fin=time(12, 0),
                defaults=dict(inicio=inicio, fin=fin, estado="confirmada"),
            )
        except IntegrityError:
            # Si el intervalo ya se ocupó por el constraint, lo ignoramos.
            pass

        self.stdout.write(self.style.SUCCESS(
            f"Demo OK → Unidades(2), Áreas(2), Copropietario(user_a101/Clave123), "
            f"Tarifa {tarifa.monto_bs} Bs, Expensas creadas {creadas}, 1 reserva."
        ))
