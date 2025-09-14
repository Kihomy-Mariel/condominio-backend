from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from django.utils import timezone
from decimal import Decimal
from datetime import date, time, datetime
from calendar import monthrange

# ==== MODELOS ====
from users.models import Rol, Usuario, CopropietarioModel, GuardiaModel
try:
    # si tienes PersonaModel
    from users.models import PersonaModel
except Exception:
    PersonaModel = None

from unidad_pertenencia.models import Unidad, Vehiculo, Mascota
from gestion_expensas.models import Tarifa, Expensa
from area_comun.models import AreaComun, Reserva
from comunicacion.models import Comunicado


class Command(BaseCommand):
    help = "Carga datos de demo: roles, admin/guardia, unidades, copropietarios, vehiculos, mascotas, tarifa/expensas, areas/reservas, visitas, comunicados."

    @transaction.atomic
    def handle(self, *args, **opts):
        resumen = []

        # ---------- ROLES ----------
        roles = {}
        for name in ["Administrador", "Guardia", "Empleado", "Copropietario"]:
            r, _ = Rol.objects.get_or_create(name=name)
            roles[name] = r
        resumen.append("Roles OK")

        # ---------- ADMIN ----------
        admin, created = Usuario.objects.get_or_create(
            username="admin",
            defaults=dict(
                email="admin@example.com",
                nombre="Administrador del sistema",
                ci="ADM-000",
                telefono="70000000",
                idRol=roles["Administrador"],
                is_staff=True,
                is_superuser=True,
            ),
        )
        if created:
            admin.set_password("Admin123!"); admin.save()
            resumen.append("Admin creado (admin / Admin123!)")
        else:
            # Asegura flags y rol
            admin.idRol = roles["Administrador"]
            admin.is_staff = True
            admin.is_superuser = True
            admin.save(update_fields=["idRol", "is_staff", "is_superuser"])
            resumen.append("Admin verificado")

        # ---------- Guardia ----------
        guard_user, g_created = Usuario.objects.get_or_create(
            username="guardia1",
            defaults=dict(
                email="guardia1@example.com",
                nombre="Guardia Uno",
                ci="G-0001",
                telefono="70000001",
                idRol=roles["Guardia"],
                is_staff=False,
                is_superuser=False,
            ),
        )
        if g_created:
            guard_user.set_password("Clave123"); guard_user.save()
        # crear/asegurar modelo guardia
        guard_defaults = {}
        # si tu GuardiaModel tiene campo 'turno'
        if "turno" in [f.name for f in GuardiaModel._meta.get_fields()]:
            guard_defaults["turno"] = "noche"
        GuardiaModel.objects.get_or_create(idUsuario=guard_user, defaults=guard_defaults)
        resumen.append("Guardia OK (guardia1 / Clave123)")

        # ---------- Unidades ----------
        unidades_datos = [
            dict(codigo="A-101", bloque="A", piso=1, numero="101", area_m2=Decimal("85.50"), estado="activa", tipo_unidad="apartamento"),
            dict(codigo="A-102", bloque="A", piso=1, numero="102", area_m2=Decimal("78.00"), estado="activa", tipo_unidad="apartamento"),
            dict(codigo="B-201", bloque="B", piso=2, numero="201", area_m2=Decimal("95.20"), estado="activa", tipo_unidad="apartamento"),
        ]
        unidades = {}
        for d in unidades_datos:
            u, _ = Unidad.objects.get_or_create(codigo=d["codigo"], defaults=d)
            unidades[u.codigo] = u
        resumen.append(f"Unidades OK ({', '.join(unidades.keys())})")

        # ---------- Copropietarios (1 por unidad) ----------
        # soporta CopropietarioModel.unidad CharField ó FK
        copro_usuarios = {}
        for cod, u in unidades.items():
            username = f"user_{cod.replace('-', '').lower()}"
            user, created = Usuario.objects.get_or_create(
                username=username,
                defaults=dict(
                    email=f"{username}@example.com",
                    nombre=f"Titular {cod}",
                    ci=f"C-{cod}",
                    telefono="70011111",
                    idRol=roles["Copropietario"],
                ),
            )
            if created:
                user.set_password("Clave123"); user.save()
            cp, _ = CopropietarioModel.objects.get_or_create(idUsuario=user)
            # asigna unidad según el esquema de tu modelo
            if hasattr(cp, "unidad_id"):      # FK
                if not cp.unidad_id:
                    cp.unidad = u
                    cp.save(update_fields=["unidad"])
            else:                              # CharField
                if not getattr(cp, "unidad", None):
                    cp.unidad = u.codigo
                    cp.save(update_fields=["unidad"])
            copro_usuarios[cod] = (user, cp)
        resumen.append("Copropietarios OK (password: Clave123)")

        # ---------- Vehículos & Mascotas ----------
        for cod, u in unidades.items():
            # Vehículos
            Vehiculo.objects.get_or_create(
                placa=f"{cod.replace('-', '')}X",
                defaults=dict(
                    marca="Toyota", modelo="Yaris", color="Rojo",
                    tag_codigo=f"TAG-{cod.replace('-', '')}",
                    estado="activo", tipo_vehiculo="automovil",
                    unidad=u,
                ),
            )
            # Mascotas
            Mascota.objects.get_or_create(
                nombre=f"Firulais-{cod.split('-')[1]}",
                defaults=dict(
                    tipo_mascota="perro", raza="Mestizo", color="Marrón",
                    peso_kg=Decimal("12.5"),
                    unidad=u, activo=True, acceso_bloqueado=False,
                ),
            )
        resumen.append("Vehículos y Mascotas OK")

        # ---------- Tarifa & Expensas (mes actual) ----------
        hoy = timezone.localdate()
        periodo = date(hoy.year, hoy.month, 1)
        tarifa, _ = Tarifa.objects.get_or_create(
            nombre="Cuota mensual",
            vigente_desde=periodo,
            defaults=dict(monto_bs=Decimal("300.00"), activa=True),
        )
        venc = date(periodo.year, periodo.month, monthrange(periodo.year, periodo.month)[1])
        creadas = 0
        for u in unidades.values():
            _, created = Expensa.objects.get_or_create(
                unidad=u, periodo=periodo,
                defaults=dict(
                    vencimiento=venc,
                    monto_total=tarifa.monto_bs,
                    saldo=tarifa.monto_bs,
                    estado="PENDIENTE",
                    glosa=f"{tarifa.nombre} {periodo:%Y-%m}",
                ),
            )
            creadas += int(created)
        resumen.append(f"Tarifa/Expensas OK (expensas nuevas: {creadas})")

        # ---------- Áreas Comunes ----------
        salon, _ = AreaComun.objects.get_or_create(
            nombre_area="Salón de Eventos",
            defaults=dict(
                capacidad=50, requiere_pago=False, precio_por_bloque=Decimal("0.00"),
                apertura_hora=time(8, 0), cierre_hora=time(22, 0),
                dias_habiles="0,1,2,3,4,5,6", estado="activo",
            ),
        )
        churras, _ = AreaComun.objects.get_or_create(
            nombre_area="Churrasquera",
            defaults=dict(
                capacidad=20, requiere_pago=False, precio_por_bloque=Decimal("0.00"),
                apertura_hora=time(9, 0), cierre_hora=time(21, 0),
                dias_habiles="0,1,2,3,4,5,6", estado="activo",
            ),
        )
        resumen.append("Áreas Comunes OK (Salón, Churrasquera)")

        # ---------- Reserva demo (mañana 10:00-12:00, anti-solape ON) ----------
        maniana = hoy + timezone.timedelta(days=1)
        tz = timezone.get_current_timezone()
        inicio = timezone.make_aware(datetime.combine(maniana, time(10, 0)), tz)
        fin    = timezone.make_aware(datetime.combine(maniana, time(12, 0)), tz)
        _, cp_a101 = copro_usuarios["A-101"]  # reserva para el titular de A-101
        try:
            Reserva.objects.get_or_create(
                usuario=cp_a101, area_comun=salon, fecha=maniana,
                hora_inicio=time(10, 0), hora_fin=time(12, 0),
                defaults=dict(inicio=inicio, fin=fin, estado="confirmada"),
            )
            resumen.append("Reserva demo OK (mañana 10-12 en Salón)")
        except IntegrityError:
            resumen.append("Reserva demo ya existía (anti-solape)")

        # ---------- Visitas (Autorizaciones) ----------
        try:
            if PersonaModel:
                fields = {f.name for f in PersonaModel._meta.get_fields()}
                persona_defaults = {"nombre": "Juan", "apellido": "Pérez"}
                if "documento" in fields:
                    persona_defaults["documento"] = "VP-1001"
                if "ci" in fields:
                    persona_defaults["ci"] = "VP-1001"
                if "telefono" in fields:
                    persona_defaults["telefono"] = "70022222"
                visitante, _ = PersonaModel.objects.get_or_create(
                    **{k: v for k, v in persona_defaults.items()}
                )

                # Crear autorización pendiente para mañana 09:00-10:00
                from area_comun.models import AutorizacionVisita
                inicio_vis = timezone.make_aware(datetime.combine(maniana, time(9, 0)), tz)
                fin_vis    = timezone.make_aware(datetime.combine(maniana, time(10, 0)), tz)
                AutorizacionVisita.objects.get_or_create(
                    visitante=visitante,
                    copropietario=cp_a101,
                    hora_inicio=inicio_vis,
                    hora_fin=fin_vis,
                    defaults=dict(estado="pendiente", motivo_visita="Mantenimiento"),
                )
                resumen.append("Visita/Autorización OK (pendiente)")
            else:
                resumen.append("PersonaModel no disponible: omito Visitas.")
        except Exception as e:
            resumen.append(f"Visitas: omitido ({e})")

        # ---------- Comunicados ----------
        Comunicado.objects.get_or_create(
            titulo="Corte de agua programado",
            defaults=dict(
                descripcion="Se interrumpirá el servicio de 14:00 a 18:00.",
                imagen_url=None,
                fecha_vencimiento=hoy + timezone.timedelta(days=7),
                tipo="COMUNICADO",
                administrador=admin,
                activo=True,
            ),
        )
        Comunicado.objects.get_or_create(
            titulo="Normas de convivencia",
            defaults=dict(
                descripcion="Recordatorio de normas y horarios de silencio.",
                imagen_url=None,
                fecha_vencimiento=hoy + timezone.timedelta(days=30),
                tipo="ANUNCIO",
                administrador=admin,
                activo=True,
            ),
        )
        resumen.append("Comunicados OK (2)")

        # ---------- Resumen ----------
        self.stdout.write(self.style.SUCCESS("Seed FULL ejecutado correctamente:\n- " + "\n- ".join(resumen)))
