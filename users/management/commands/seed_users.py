from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from users.models import Rol

User = get_user_model()

class Command(BaseCommand):
    help = "Crea roles base y un superusuario con idRol asignado (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin")
        parser.add_argument("--email", default="admin@example.com")
        parser.add_argument("--password", default="Admin123!Cambiar")
        parser.add_argument("--nombre", default="Administrador del sistema")
        parser.add_argument("--ci", default="00000000")
        parser.add_argument("--telefono", default="")
        parser.add_argument("--rol", default="Administrador")
        parser.add_argument("--force-reset", action="store_true",
                            help="Si el usuario ya existe, actualiza password, email, rol y flags.")

    @transaction.atomic
    def handle(self, *args, **opts):
        username   = opts["username"]
        email      = opts["email"]
        password   = opts["password"]
        nombre     = opts["nombre"]
        ci         = opts["ci"]
        telefono   = opts["telefono"]
        rol_nombre = opts["rol"]
        force      = opts["force_reset"]

        # 1) Roles base
        for r in ["Administrador", "Empleado", "Copropietario"]:
            Rol.objects.get_or_create(name=r)
        rol_admin, _ = Rol.objects.get_or_create(name=rol_nombre)

        # 2) Superusuario con idRol (y campos obligatorios)
        try:
            u = User.objects.get(username=username)
            creado = False
            if force:
                u.email = email
                u.nombre = nombre
                u.ci = ci
                u.telefono = telefono or u.telefono
                u.is_staff = True
                u.is_superuser = True
                setattr(u, "idRol", rol_admin)   # FK NOT NULL
                u.set_password(password)
                u.save()
        except User.DoesNotExist:
            creado = True
            u = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                nombre=nombre,         # <-- campos extra requeridos por tu modelo
                ci=ci,
                telefono=telefono or None,
                idRol=rol_admin,       # <-- CLAVE: tu FK NOT NULL (db_column=idrol)
            )

        estado = "creado" if creado else ("actualizado" if force else "existente")
        self.stdout.write(self.style.SUCCESS(
            f"Roles OK. Superusuario '{username}' {estado} con rol '{rol_admin.name}'."
        ))
