# unidad_pertenencia/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

def _rol_nombre(user) -> str:
    return getattr(getattr(user, 'idRol', None), 'name', '') or ''

class AdminOrStaffReadOnly(BasePermission):
    """
    - GET/HEAD/OPTIONS permitidos a: Administrador, Guardia, Empleado
    - Métodos de escritura (POST/PUT/PATCH/DELETE) solo: Administrador
    """
    def has_permission(self, request, view):
        role = _rol_nombre(request.user)
        if request.method in SAFE_METHODS:
            return role in ('Administrador', 'Guardia', 'Empleado')
        return role == 'Administrador'
