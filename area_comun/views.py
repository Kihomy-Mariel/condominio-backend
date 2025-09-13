from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view,action
from rest_framework.response import Response
from datetime import datetime
from .models import AreaComun, Reserva, AutorizacionVisita
from .serializers import MarcarEntradaSerializer, MarcarSalidaSerializer,AreaComunSerializer, ReservaSerializer, ListaVisitantesSerializer
from rest_framework.parsers import MultiPartParser, FormParser

# #Crear Lista Invitados


# @api_view(['POST'])
# def crearListaInvitados(request):

# MOSTRAR VISITAS PARA EL GUARDIA
@api_view(['GET'])
def mostrarVisitas(request):
    visitas = AutorizacionVisita.objects.all()
    visitas_serializadas = ListaVisitantesSerializer(visitas, many=True).data

    data = []
    for visita in visitas_serializadas:
        data.append({
            "nombre": visita["nombre"],
            "apellido": visita["apellido"],
            "CI": visita["ci"],
            "fecha_inicio": visita["hora_inicio"],
            "fecha_fin": visita["hora_fin"],
            "motivo_visita": visita["motivo_visita"],
            "estado": visita["estado"],
        })

    return Response({
        "status": 1,
        "error": 0,
        "message": "Visitas listadas correctamente",
        "data": data
    })
# Create your views here.
@api_view(['GET'])
def mostrarCalendarioAreasComunes(request):
    # Obtener fecha del body
    fecha_str = request.data.get("fecha")
    if not fecha_str:
        return Response({
            "status": 2,
            "error": 1,
            "message": "Debe enviar una fecha en formato YYYY-MM-DD",
        })

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return Response({
            "status": 2,
            "error": 1,
            "message": "Formato de fecha inválido, use YYYY-MM-DD",
        })

    data = {"disponibles": [], "ocupados": []}

    for area in AreaComun.objects.all():
        # Obtener horario de apertura/cierre de la zona
        horario_inicio = timezone.make_aware(datetime.combine(fecha, area.apertura_hora))
        horario_fin = timezone.make_aware(datetime.combine(fecha, area.cierre_hora))

        # Traer reservas del día
        reservas = Reserva.objects.filter(
            area_comun=area,
            fecha=fecha,
            estado='confirmada'  # Solo considerar reservas confirmadas
        ).order_by("hora_inicio")

        ocupados = []
        libres = []
        current_time = horario_inicio

        for r in reservas:
            # Combinar fecha y hora para datetime aware
            inicio_dt = timezone.make_aware(datetime.combine(r.fecha, r.hora_inicio))
            fin_dt = timezone.make_aware(datetime.combine(r.fecha, r.hora_fin))

            # Añadir a ocupados
            ocupados.append({
                "hora_inicio": inicio_dt.strftime("%H:%M"),
                "hora_fin": fin_dt.strftime("%H:%M")
            })

            # Hueco libre antes de esta reserva
            if inicio_dt > current_time:
                libres.append({
                    "hora_inicio": current_time.strftime("%H:%M"),
                    "hora_fin": inicio_dt.strftime("%H:%M")
                })

            # Avanzar current_time al final de la reserva
            if fin_dt > current_time:
                current_time = fin_dt

        # Último hueco hasta cierre del área
        if current_time < horario_fin:
            libres.append({
                "hora_inicio": current_time.strftime("%H:%M"),
                "hora_fin": horario_fin.strftime("%H:%M")
            })

        data["ocupados"].append({"area_comun": area.nombre_area, "horarios": ocupados})
        data["disponibles"].append({"area_comun": area.nombre_area, "horarios": libres})

    return Response({
        "status": 1,
        "error": 0,
        "message": "Calendario de áreas comunes",
        "data": data
    })

@api_view(['PATCH'])
def marcarEntradaVisita(request):
    serializer = MarcarEntradaSerializer(data=request.data)
    if serializer.is_valid():
        resultado = serializer.save()
        visitante = resultado['visitante']
        registro = resultado['registro']
        return Response({
            "status": 1,
            "error": 0,
            "message": f"Entrada registrada para {visitante.nombre} {visitante.apellido} a las {registro.fecha_entrada}."
        })
    return Response({
        "status": 2,
        "error": 1,
        "message": serializer.errors
    })


@api_view(['PATCH'])
def marcarSalidaVisita(request):
    serializer = MarcarSalidaSerializer(data=request.data)
    if serializer.is_valid():
        resultado = serializer.save()
        visitante = resultado['visitante']
        registro = resultado['registro']
        return Response({
            "status": 1,
            "error": 0,
            "message": f"Salida registrada para {visitante.nombre} {visitante.apellido} a las {registro.fecha_salida}."
        })
    return Response({
        "status": 2,
        "error": 1,
        "message": serializer.errors
    })

class AreaComunViewSet(viewsets.ModelViewSet):
    queryset = AreaComun.objects.all()
    serializer_class = AreaComunSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def list(self, request, *args, **kwargs):
        areas = self.get_queryset()
        serializer = self.get_serializer(areas, many=True)
        return Response({
            "Status": 1,
            "Error": 0,
            "message": "Áreas listadas correctamente",
            "data": serializer.data
        })
    def destroy(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.rol_id != 1:
            return Response({
                "Status": 0,
                "Error": 1,
                "message": "No tienes permisos para eliminar áreas comunes",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance = self.get_object()
        instance.activa = False
        instance.estado = 'inactivo'
        instance.save()

        return Response({
            "Status": 1,
            "Error": 0,
            "message": f"Área con id {instance.pk} eliminada correctamente",
            "data": {}
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        #Validar si es Admin
        if not request.user.is_authenticated or request.user.rol_id != 1:
            return Response({
                "Status": 0,
                "Error": 1,
                "message": "No tienes permisos para crear áreas comunes",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "Status": 1,
            "Error": 0,
            "message": "Área creada correctamente",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser] 

    def list(self, request, *args, **kwargs):
        reservas = self.get_queryset()
        serializer = self.get_serializer(reservas, many=True)
        return Response({
            "Status": 1,
            "Error": 0,
            "message": "Reservas listadas correctamente",
            "data": serializer.data
        })

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "Status": 1,
            "Error": 0,
            "message": "Reserva creada correctamente",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancelar(self, request, pk=None):
        reserva = self.get_object()
        if reserva.estado == 'cancelada':
            return Response({
                "Status": 2,
                "Error": 1,
                "message": "La reserva ya está cancelada",
                "data": {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        motivo = request.data.get('motivo_cancelacion', '')
        reserva.estado = 'cancelada'
        reserva.cancelada_en = timezone.now()
        reserva.motivo_cancelacion = motivo
        reserva.save()

        serializer = self.get_serializer(reserva)
        return Response({
            "Status": 1,
            "Error": 0,
            "message": "Reserva cancelada correctamente",
            "data": serializer.data
            })