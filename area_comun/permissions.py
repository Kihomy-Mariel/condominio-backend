from rest_framework.permissions import BasePermission, SAFE_METHODS

def _rol(u) -> str:
    return getattr(getattr(u, 'idRol', None), 'name', '') or ''

class AdminOrStaffReadOnly(BasePermission):
    """
    - GET/HEAD/OPTIONS: Administrador, Guardia, Empleado, Copropietario (pueden leer)
    - POST/PUT/PATCH/DELETE: solo Administrador
    """
    def has_permission(self, request, view):
        role = _rol(request.user)
        if request.method in SAFE_METHODS:
            return role in ('Administrador','Guardia','Empleado','Copropietario')
        return role == 'Administrador'

class CopropietarioOrAdmin(BasePermission):
    """
    Crear/cancelar reservas: Copropietario (sobre las suyas) o Admin.
    (La verificación de "dueño" se hace en la vista)
    """
    def has_permission(self, request, view):
        role = _rol(request.user)
        if request.method in SAFE_METHODS:
            return role in ('Administrador','Guardia','Empleado','Copropietario')
        return role in ('Administrador','Copropietario')

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(
            u and u.is_authenticated and
            getattr(getattr(u, "idRol", None), "name", "") == "Administrador"
        )