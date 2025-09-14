from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from users.models import Rol

User = get_user_model()

ROLES_BASE = ["Administrador", "Guardia", "Empleado", "Copropietario"]

class Command(BaseCommand):
    help = "Crea roles base y un superusuario con idRol asignado (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin")
        parser.add_argument("--email", default="admin@example.com")
        parser.add_argument("--password", default="clave123")
        parser.add_argument("--nombre", default="Administrador del sistema")
        parser.add_argument("--ci", default="00000000")
        parser.add_argument("--telefono", default="")
        parser.add_argument("--rol", default="Administrador",
                            help="Nombre del rol a asignar al usuario (debe existir en ROLES_BASE).")
        parser.add_argument("--force-reset", action="store_true",
                            help="Si el usuario ya existe, actualiza password, email, rol y flags.")

    @transaction.atomic
    def handle(self, *args, **opts):
        username   = opts["username"]
        email      = opts["email"]
        password   = opts["password"]
        nombre     = opts["nombre"]
        ci         = opts["ci"]
        telefono   = opts["telefono"] or None
        rol_nombre = opts["rol"]
        force      = opts["force_reset"]

        # 1) Crear roles base (idempotente)
        for r in ROLES_BASE:
            Rol.objects.get_or_create(name=r)

        try:
            rol_obj = Rol.objects.get(name=rol_nombre)
        except Rol.DoesNotExist:
            return self._fail(f"El rol '{rol_nombre}' no existe. Usa uno de: {', '.join(ROLES_BASE)}")

        # 2) Superusuario con idRol (y campos obligatorios)
        creado = False
        try:
            u = User.objects.get(username=username)
            if force:
                u.email = email
                u.nombre = nombre
                u.ci = ci
                u.telefono = telefono if telefono is not None else u.telefono
                u.is_staff = True
                u.is_superuser = True
                setattr(u, "idRol", rol_obj)  # asigna FK de rol
                u.set_password(password)
                u.save()
                estado = "actualizado"
            else:
                estado = "existente"
        except User.DoesNotExist:
            u = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                nombre=nombre,       # campos extra de tu modelo
                ci=ci,
                telefono=telefono,
                idRol=rol_obj,       # FK (db_column=idrol)
            )
            creado = True
            estado = "creado"

        self.stdout.write(self.style.SUCCESS(
            f"Roles OK ({', '.join(ROLES_BASE)}). Superusuario '{username}' {estado} con rol '{rol_obj.name}'."
        ))

    def _fail(self, msg: str):
        self.stderr.write(self.style.ERROR(msg))
