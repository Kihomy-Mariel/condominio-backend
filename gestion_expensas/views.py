from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from users.models import CopropietarioModel
from .models import Expensa, Pago
from .serializers import ExpensaSerializer, PagoCreateSerializer
from .permissions import IsAdmin

# ---------- Helpers de respuesta ----------
def ok(message="OK", data=None, status_code=status.HTTP_200_OK):
    return Response({"ERROR": 0, "STATUS": 1, "MESSAGE": message, "data": data}, status=status_code)

def fail(message="Error", data=None, status_code=status.HTTP_400_BAD_REQUEST, error_code=1):
    return Response({"ERROR": error_code, "STATUS": 2, "MESSAGE": message, "data": data}, status=status_code)


class MisExpensasList(generics.ListAPIView):
    """
    CU09: Copropietario ve sus expensas.
    Busca códigos de unidad en CopropietarioModel.unidad (CharField) del usuario autenticado
    y filtra Expensa por unidad__codigo IN esos códigos.
    """
    serializer_class = ExpensaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        codigos = list(
            CopropietarioModel.objects.filter(idUsuario=u).values_list("unidad", flat=True)
        )
        return Expensa.objects.filter(unidad__codigo__in=codigos).order_by("-periodo")

    # Envolver respuesta
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return ok(message=f"Se encontraron {len(serializer.data)} expensas", data=serializer.data)


class CrearPagoView(generics.CreateAPIView):
    """
    CU07: sube comprobante; queda PENDIENTE.
    Valida que la expensa pertenezca a alguna de sus unidades.
    """
    serializer_class = PagoCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    # Envolver respuesta de creación y capturar validación/permiso
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return fail(message="Datos inválidos para registrar el pago", data=serializer.errors)

        try:
            self.perform_create(serializer)
        except PermissionDenied as e:
            return fail(message=str(e), status_code=status.HTTP_403_FORBIDDEN)

        headers = self.get_success_headers(serializer.data)
        return ok(message="Pago registrado correctamente", data=serializer.data, status_code=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        u = self.request.user
        expensa = serializer.validated_data["expensa"]
        codigos = list(
            CopropietarioModel.objects.filter(idUsuario=u).values_list("unidad", flat=True)
        )
        if expensa.unidad.codigo not in codigos:
            raise PermissionDenied("No puedes pagar expensas de otra unidad.")
        serializer.save()


class PagosDeExpensaList(generics.ListAPIView):
    serializer_class = PagoCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        expensa_id = self.kwargs["pk"]
        return Pago.objects.filter(expensa_id=expensa_id).order_by("-created_at")

    # Envolver respuesta
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return ok(message=f"{len(serializer.data)} pagos encontrados", data=serializer.data)


class AprobarPagoSimple(APIView):
    """
    CU08: Admin aprueba un pago (cambia estado y ajusta saldo via signals).
    """
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            p = Pago.objects.get(pk=pk)
        except Pago.DoesNotExist:
            return fail(message="Pago no existe.", status_code=status.HTTP_404_NOT_FOUND)

        if p.estado != "APROBADO":
            p.estado = "APROBADO"
            p.save(update_fields=["estado"])

        return ok(message="Pago aprobado", data={"id": p.id, "estado": p.estado})
