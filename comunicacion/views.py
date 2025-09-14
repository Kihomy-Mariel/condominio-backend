from rest_framework import viewsets, status, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Comunicado
from .serializers import ComunicadoSerializer, ListarComunicadoSerializer
from .permissions import IsAdmin

class ComunicadoViewSet(viewsets.ModelViewSet):
    """
    - List (GET): todos los roles autenticados ven comunicados activos (por defecto).
                  ?todos=1 para ver también inactivos (solo admin).
    - Create/Update/Delete: solo Administrador.
    - Delete: borrado lógico -> activo=False (no se borra físicamente).
    """
    queryset = Comunicado.objects.all()
    serializer_class = ComunicadoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["titulo", "descripcion", "tipo"]
    ordering_fields = ["fecha_publicacion", "fecha_vencimiento", "id"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "activar", "archivar"]:
            return [permissions.IsAuthenticated(), IsAdmin()]
        # list/retrieve: cualquier autenticado
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ListarComunicadoSerializer
        return ComunicadoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        todos = self.request.query_params.get("todos")
        if todos == "1":
            # Solo admin puede ver todos (activos e inactivos)
            if IsAdmin().has_permission(self.request, self):
                return qs
        # Por defecto, solo activos
        return qs.filter(activo=True)

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        self.perform_create(ser)
        return Response(
            {"status": 1, "error": 0, "message": "Comunicado creado correctamente", "values": ser.data},
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        resp = super().update(request, *args, **kwargs)
        return Response({"status": 1, "error": 0, "message": "Comunicado actualizado", "values": resp.data})

    def partial_update(self, request, *args, **kwargs):
        resp = super().partial_update(request, *args, **kwargs)
        return Response({"status": 1, "error": 0, "message": "Comunicado actualizado", "values": resp.data})

    def destroy(self, request, *args, **kwargs):
        """
        Borrado lógico: activo=False
        """
        instance = self.get_object()
        instance.activo = False
        instance.save(update_fields=["activo"])
        return Response({"status": 1, "error": 0, "message": "Comunicado eliminado (inactivado)"})

    # Atajos útiles:
    @action(detail=True, methods=["post"])
    def archivar(self, request, pk=None):
        obj = self.get_object()
        obj.activo = False
        obj.save(update_fields=["activo"])
        return Response({"status": 1, "error": 0, "message": "Comunicado archivado"})

    @action(detail=True, methods=["post"])
    def activar(self, request, pk=None):
        obj = self.get_object()
        obj.activo = True
        obj.save(update_fields=["activo"])
        return Response({"status": 1, "error": 0, "message": "Comunicado activado"})
