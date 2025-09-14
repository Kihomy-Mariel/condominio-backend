from rest_framework.permissions import BasePermission, SAFE_METHODS

def _rol_name(u) -> str:
    return getattr(getattr(u, "idRol", None), "name", "") or ""

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and _rol_name(u) == "Administrador")

class AdminOrStaffReadOnly(BasePermission):
    """
    Lectura (GET/HEAD/OPTIONS): Admin, Guardia, Empleado
    Escritura (POST/PUT/PATCH/DELETE): solo Admin
    """
    def has_permission(self, request, view):
        role = _rol_name(request.user)
        if request.method in SAFE_METHODS:
            return role in ("Administrador", "Guardia", "Empleado")
        return role == "Administrador"
