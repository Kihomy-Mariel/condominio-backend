from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import AreaComun, Reserva, AutorizacionVisita, RegistroVisitaModel
from .serializers import (
    AreaComunSerializer, ReservaSerializer,
    MarcarEntradaSerializer, MarcarSalidaSerializer,
    ListaVisitantesSerializer
)
from .permissions import AdminOrStaffReadOnly, CopropietarioOrAdmin, IsAdmin
from users.models import CopropietarioModel, GuardiaModel, PersonaModel

# ---------- helpers envelope ----------
def ok(message="OK", values=None, code=status.HTTP_200_OK):
    return Response({"status":1,"error":0,"message":message,"values":values}, status=code)

def fail(message="Error", values=None, code=status.HTTP_400_BAD_REQUEST):
    return Response({"status":2,"error":1,"message":message,"values":values}, status=code)


# ===================== VISITAS (guardia) =====================

@api_view(['GET'])
def mostrarVisitas(request):
    visitas = AutorizacionVisita.objects.all().order_by('-hora_inicio')
    data = ListaVisitantesSerializer(visitas, many=True).data
    return Response({
        "status": 1,
        "error": 0,
        "message": "Visitas listadas correctamente",
        "data": data
    })

@api_view(['PATCH'])
def marcarEntradaVisita(request):
    serializer = MarcarEntradaSerializer(data=request.data)
    if serializer.is_valid():
        res = serializer.save()
        visitante = res['visitante']
        reg = res['registro']
        return ok(f"Entrada registrada para {visitante.nombre} {visitante.apellido} a las {reg.fecha_entrada}.")
    return fail("Datos inválidos", serializer.errors)

@api_view(['PATCH'])
def marcarSalidaVisita(request):
    serializer = MarcarSalidaSerializer(data=request.data)
    if serializer.is_valid():
        res = serializer.save()
        visitante = res['visitante']
        reg = res['registro']
        return ok(f"Salida registrada para {visitante.nombre} {visitante.apellido} a las {reg.fecha_salida}.")
    return fail("Datos inválidos", serializer.errors)


# ===================== AREAS =====================

class AreaComunViewSet(viewsets.ModelViewSet):
    queryset = AreaComun.objects.all().order_by('nombre_area')
    serializer_class = AreaComunSerializer
    permission_classes = [permissions.IsAuthenticated, AdminOrStaffReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre_area']
    ordering_fields = ['nombre_area','capacidad']

    def list(self, request, *args, **kwargs):
        ser = self.get_serializer(self.get_queryset(), many=True)
        return ok("Áreas listadas correctamente", ser.data)

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        if ser.is_valid():
            self.perform_create(ser)
            return ok("Área creada correctamente", ser.data, code=status.HTTP_201_CREATED)
        return fail("Datos inválidos para crear el área", ser.errors)

    def update(self, request, *args, **kwargs):
        ser = self.get_serializer(self.get_object(), data=request.data, partial=False)
        if ser.is_valid():
            self.perform_update(ser)
            return ok("Área actualizada correctamente", ser.data)
        return fail("Datos inválidos para actualizar el área", ser.errors)

    def partial_update(self, request, *args, **kwargs):
        ser = self.get_serializer(self.get_object(), data=request.data, partial=True)
        if ser.is_valid():
            self.perform_update(ser)
            return ok("Área actualizada correctamente", ser.data)
        return fail("Datos inválidos para actualizar el área", ser.errors)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.estado = 'inactivo'
        instance.save(update_fields=['estado'])
        return ok(f"Área '{instance.nombre_area}' desactivada")

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def disponibilidad(self, request, pk=None):
        """
        GET /areacomun/areas/{id}/disponibilidad/?fecha=YYYY-MM-DD
        Devuelve bloques libres y ocupados para ese día.
        """
        area = self.get_object()
        fecha_str = request.query_params.get('fecha')
        if not fecha_str:
            return fail("Debe enviar ?fecha=YYYY-MM-DD")
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            return fail("Formato de fecha inválido, use YYYY-MM-DD")

        if area.estado != 'activo':
            return fail("El área no está activa")

        if not area.dia_habil(fecha):
            return ok("Día no habilitado para el área", {"ocupados": [], "libres": []})

        tz = timezone.get_current_timezone()
        apertura = timezone.make_aware(datetime.combine(fecha, area.apertura_hora), tz)
        cierre   = timezone.make_aware(datetime.combine(fecha, area.cierre_hora), tz)

        reservas = (Reserva.objects
                    .filter(area_comun=area, fecha=fecha, estado__in=['pendiente','confirmada'])
                    .order_by('hora_inicio'))

        ocupados = []
        libres = []

        current = apertura
        for r in reservas:
            ini = timezone.make_aware(datetime.combine(r.fecha, r.hora_inicio), tz)
            fin = timezone.make_aware(datetime.combine(r.fecha, r.hora_fin), tz)

            # hueco libre antes
            if ini > current:
                libres.append({"hora_inicio": current.strftime("%H:%M"), "hora_fin": ini.strftime("%H:%M")})
            # bloque ocupado
            ocupados.append({"hora_inicio": ini.strftime("%H:%M"), "hora_fin": fin.strftime("%H:%M")})
            if fin > current:
                current = fin

        if current < cierre:
            libres.append({"hora_inicio": current.strftime("%H:%M"), "hora_fin": cierre.strftime("%H:%M")})

        return ok("Disponibilidad del área", {"area": area.nombre_area, "fecha": fecha_str, "ocupados": ocupados, "libres": libres})

class AreaComunViewSet(viewsets.ModelViewSet):
    queryset = AreaComun.objects.all()
    serializer_class = AreaComunSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        # list/retrieve: lectura
        return [permissions.IsAuthenticatedOrReadOnly()]


# ===================== RESERVAS =====================

class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.select_related('area_comun','usuario__idUsuario').all().order_by('-creada_en')
    serializer_class = ReservaSerializer
    permission_classes = [permissions.IsAuthenticated, CopropietarioOrAdmin]
    parser_classes = [MultiPartParser, FormParser]  # por si luego anexas comprobante archivo

    def get_queryset(self):
        qs = super().get_queryset()
        # Copropietario: solo sus reservas
        try:
            coprop = CopropietarioModel.objects.get(idUsuario=self.request.user)
            return qs.filter(usuario=coprop)
        except CopropietarioModel.DoesNotExist:
            # Admin/Guardia/Empleado ven todo
            return qs

    def list(self, request, *args, **kwargs):
        ser = self.get_serializer(self.get_queryset(), many=True)
        return ok("Reservas listadas correctamente", ser.data)

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        if ser.is_valid():
            try:
                self.perform_create(ser)
                return ok("Reserva creada correctamente", ser.data, code=status.HTTP_201_CREATED)
            except Exception as e:
                return fail(str(e))
        return fail("Datos inválidos para crear la reserva", ser.errors)

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """
        Copropietario puede cancelar su reserva; Admin puede cancelar cualquiera.
        """
        reserva = self.get_object()

        # permiso: si es coprop, debe ser suya
        role = getattr(getattr(request.user, 'idRol', None), 'name', '')
        if role == 'Copropietario':
            try:
                cop = CopropietarioModel.objects.get(idUsuario=request.user)
            except CopropietarioModel.DoesNotExist:
                return fail("No eres copropietario")
            if reserva.usuario_id != cop.id:
                return fail("No puedes cancelar reservas de otro usuario", code=status.HTTP_403_FORBIDDEN)

        if reserva.estado == 'cancelada':
            return fail("La reserva ya está cancelada", code=status.HTTP_400_BAD_REQUEST)

        reserva.estado = 'cancelada'
        reserva.cancelada_en = timezone.now()
        reserva.save(update_fields=['estado','cancelada_en'])

        ser = self.get_serializer(reserva)
        return ok("Reserva cancelada correctamente", ser.data)
