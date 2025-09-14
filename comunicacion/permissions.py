from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """
    Solo deja pasar si el usuario autenticado tiene rol 'Administrador'.
    """
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        rol = getattr(getattr(u, "idRol", None), "name", "")
        return bool(u and u.is_authenticated and rol == "Administrador")
