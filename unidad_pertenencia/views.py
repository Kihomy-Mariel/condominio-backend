# unidad_pertenencia/views.py
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Unidad, Vehiculo, Mascota
from .serializers import UnidadSerializer, VehiculoSerializer, MascotaSerializer
from .permissions import AdminOrStaffReadOnly
from users.models import CopropietarioModel  # para filtrar por unidad del copropietario

def _ok(message: str, values=None, code=status.HTTP_200_OK):
    return Response({"status": 1, "error": 0, "message": message, "values": values}, status=code)

def _bad(message: str, errors=None, code=status.HTTP_400_BAD_REQUEST):
    body = {"status": 2, "error": 1, "message": message}
    if errors is not None:
        body["errors"] = errors
    return Response(body, status=code)

def _rol_nombre(user) -> str:
    return getattr(getattr(user, 'idRol', None), 'name', '') or ''


class UnidadViewSet(viewsets.ModelViewSet):
    queryset = Unidad.objects.all().order_by('bloque', 'piso', 'numero')
    serializer_class = UnidadSerializer
    authentication_classes = []  # usa las globales del settings (JWT)
    permission_classes = [IsAuthenticated, AdminOrStaffReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['codigo', 'bloque', 'numero', 'tipo_unidad']
    filterset_fields = ['estado', 'tipo_unidad', 'bloque', 'piso']
    ordering_fields = ['id', 'bloque', 'piso', 'numero', 'created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        role = _rol_nombre(self.request.user)
        # Si es Copropietario: solo su(s) unidad(es)
        if role == 'Copropietario':
            unidad_ids = (CopropietarioModel.objects
                          .filter(idUsuario=self.request.user)
                          .values_list('unidad_id', flat=True))
            qs = qs.filter(id__in=unidad_ids)
        return qs

    # Envoltorios del response
    def list(self, request, *args, **kwargs):
        resp = super().list(request, *args, **kwargs)
        return _ok(f"Se encontraron {len(resp.data)} unidades", resp.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.get_serializer(instance).data
        return _ok(f"Detalles de la unidad {instance.codigo}", data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # unicidad de codigo ya se valida por unique=True en el modelo,
            # pero enviamos un mensaje homogéneo si falla la DB.
            try:
                instance = serializer.save()
            except Exception as e:
                return _bad("No se pudo crear la unidad (posible código duplicado).", {"detail": str(e)})
            return _ok(f"Unidad {instance.codigo} creada exitosamente", self.get_serializer(instance).data, code=status.HTTP_201_CREATED)
        return _bad("Datos inválidos para crear la unidad", serializer.errors)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            try:
                instance = serializer.save()
            except Exception as e:
                return _bad("No se pudo actualizar la unidad.", {"detail": str(e)})
            return _ok(f"Unidad {instance.codigo} actualizada", self.get_serializer(instance).data)
        return _bad("Datos inválidos para actualizar la unidad", serializer.errors)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        codigo = instance.codigo
        instance.delete()
        return _ok(f"Unidad {codigo} eliminada")


class VehiculoViewSet(viewsets.ModelViewSet):
    queryset = Vehiculo.objects.select_related('unidad').all().order_by('placa')
    serializer_class = VehiculoSerializer
    permission_classes = [IsAuthenticated, AdminOrStaffReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['placa', 'marca', 'modelo', 'color', 'tipo_vehiculo', 'tag_codigo', 'unidad__codigo']
    filterset_fields = ['estado', 'unidad']
    ordering_fields = ['id', 'placa', 'created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        role = _rol_nombre(self.request.user)
        if role == 'Copropietario':
            unidad_ids = (CopropietarioModel.objects
                          .filter(idUsuario=self.request.user)
                          .values_list('unidad_id', flat=True))
            qs = qs.filter(unidad_id__in=unidad_ids)
        return qs

    def list(self, request, *args, **kwargs):
        resp = super().list(request, *args, **kwargs)
        return _ok(f"Se encontraron {len(resp.data)} vehículos", resp.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.get_serializer(instance).data
        return _ok(f"Detalles del vehículo {instance.placa}", data)

    def create(self, request, *args, **kwargs):
        # Nota: por tus CU, en WEB solo Admin crea/edita/elimina (ya lo asegura AdminOrStaffReadOnly)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                instance = serializer.save()
            except Exception as e:
                return _bad("No se pudo registrar el vehículo (placa o tag duplicados).", {"detail": str(e)})
            return _ok(f"Vehículo {instance.placa} registrado", self.get_serializer(instance).data, code=status.HTTP_201_CREATED)
        return _bad("Datos inválidos para registrar el vehículo", serializer.errors)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            try:
                instance = serializer.save()
            except Exception as e:
                return _bad("No se pudo actualizar el vehículo.", {"detail": str(e)})
            return _ok(f"Vehículo {instance.placa} actualizado", self.get_serializer(instance).data)
        return _bad("Datos inválidos para actualizar el vehículo", serializer.errors)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                instance = serializer.save()
            except Exception as e:
                return _bad("No se pudo actualizar el vehículo.", {"detail": str(e)})
            return _ok(f"Vehículo {instance.placa} actualizado", self.get_serializer(instance).data)
        return _bad("Datos inválidos para actualizar el vehículo", serializer.errors)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        placa = instance.placa
        instance.delete()
        return _ok(f"Vehículo {placa} eliminado")


class MascotaViewSet(viewsets.ModelViewSet):
    queryset = Mascota.objects.select_related('unidad').all().order_by('nombre')
    serializer_class = MascotaSerializer
    permission_classes = [IsAuthenticated, AdminOrStaffReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'tipo_mascota', 'raza', 'color', 'unidad__codigo']
    filterset_fields = ['unidad', 'activo', 'tipo_mascota']
    ordering_fields = ['id', 'nombre', 'created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        role = _rol_nombre(self.request.user)
        if role == 'Copropietario':
            unidad_ids = (CopropietarioModel.objects
                          .filter(idUsuario=self.request.user)
                          .values_list('unidad_id', flat=True))
            qs = qs.filter(unidad_id__in=unidad_ids)
        return qs

    def list(self, request, *args, **kwargs):
        resp = super().list(request, *args, **kwargs)
        return _ok(f"Se encontraron {len(resp.data)} mascotas", resp.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.get_serializer(instance).data
        return _ok(f"Detalles de la mascota {instance.nombre}", data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                instance = serializer.save()
            except Exception as e:
                return _bad("No se pudo registrar la mascota.", {"detail": str(e)})
            return _ok(f"Mascota {instance.nombre} registrada", self.get_serializer(instance).data, code=status.HTTP_201_CREATED)
        return _bad("Datos inválidos para registrar la mascota", serializer.errors)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            try:
                instance = serializer.save()
            except Exception as e:
                return _bad("No se pudo actualizar la mascota.", {"detail": str(e)})
            return _ok(f"Mascota {instance.nombre} actualizada", self.get_serializer(instance).data)
        return _bad("Datos inválidos para actualizar la mascota", serializer.errors)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                instance = serializer.save()
            except Exception as e:
                return _bad("No se pudo actualizar la mascota.", {"detail": str(e)})
            return _ok(f"Mascota {instance.nombre} actualizada", self.get_serializer(instance).data)
        return _bad("Datos inválidos para actualizar la mascota", serializer.errors)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        nombre = instance.nombre
        instance.delete()
        return _ok(f"Mascota {nombre} eliminada")
