from datetime import date
from calendar import monthrange

from rest_framework import generics, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q, F
from django_filters.rest_framework import DjangoFilterBackend

from users.models import CopropietarioModel
from unidad_pertenencia.models import Unidad
from .models import Expensa, Pago, Tarifa
from .serializers import ExpensaSerializer, PagoCreateSerializer, PagoListSerializer
from .permissions import IsAdmin, AdminOrStaffReadOnly

# --------- Envelope unificado ----------
def ok(message="OK", values=None, status_code=status.HTTP_200_OK):
    return Response({"status": 1, "error": 0, "message": message, "values": values}, status=status_code)

def fail(message="Error", values=None, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({"status": 2, "error": 1, "message": message, "values": values}, status=status_code)

def _rol_name(u) -> str:
    return getattr(getattr(u, "idRol", None), "name", "") or ""

def _first_day_from_yyyymm(yyyymm: str) -> date:
    # "2025-09" -> date(2025, 9, 1). Si llega "2025-09-01", también sirve.
    parts = yyyymm.split("-")
    y, m = int(parts[0]), int(parts[1])
    return date(y, m, 1)

def _last_day_of_month(d: date) -> date:
    return date(d.year, d.month, monthrange(d.year, d.month)[1])


# =============== CU06: Generar expensas mensuales ===============
class GenerarExpensasMensuales(APIView):
    """
    POST body:
    {
      "periodo": "YYYY-MM",          // requerido
      "unidad_id": 123,              // opcional (si faltante => todas activas)
      "vencimiento": "YYYY-MM-DD",   // opcional (default: último día del mes)
      "sobrescribir": false          // opcional, si True y existe expensa de ese periodo, la actualiza
    }
    Reglas:
    - Usa la Tarifa activa con mayor "vigente_desde" <= periodo (si no hay, error).
    - Crea Expensa(unidad, periodo) con monto_total=tarifa, saldo=monto_total.
    - Si existe ya (unique_together), y `sobrescribir=True`, actualiza montos/fechas.
    - Solo Admin.
    """
    permission_classes = [IsAdmin]

    @transaction.atomic
    def post(self, request):
        try:
            if "periodo" not in request.data:
                return fail("Debes enviar 'periodo' como 'YYYY-MM'.")

            per = _first_day_from_yyyymm(str(request.data["periodo"]))
            ven = request.data.get("vencimiento")
            if ven:
                yyyy, mm, dd = map(int, str(ven).split("-"))
                venc = date(yyyy, mm, dd)
            else:
                venc = _last_day_of_month(per)

            sobrescribir = bool(request.data.get("sobrescribir", False))
            unidad_id = request.data.get("unidad_id")

            # Tarifa vigente
            tarifa = (Tarifa.objects
                      .filter(activa=True, vigente_desde__lte=per)
                      .order_by("-vigente_desde")
                      .first())
            if not tarifa:
                return fail("No existe una tarifa activa vigente para ese periodo.")

            if unidad_id:
                unidades = Unidad.objects.filter(pk=unidad_id, estado="activa")
            else:
                unidades = Unidad.objects.filter(estado="activa")

            creadas, actualizadas, omitidas = [], [], []
            for u in unidades.select_for_update():
                defaults = {
                    "vencimiento": venc,
                    "monto_total": tarifa.monto_bs,
                    "saldo": tarifa.monto_bs,
                    "estado": "PENDIENTE",
                    "glosa": f"{tarifa.nombre} {per:%Y-%m}",
                }
                obj, created = Expensa.objects.get_or_create(unidad=u, periodo=per, defaults=defaults)
                if created:
                    creadas.append(obj.id)
                else:
                    if sobrescribir:
                        obj.vencimiento = venc
                        obj.monto_total = tarifa.monto_bs
                        # si ya hay pagos previos, conserva saldo relativo al nuevo total
                        if obj.saldo > obj.monto_total:
                            obj.saldo = obj.monto_total
                        obj.recalc_estado()
                        obj.glosa = f"{tarifa.nombre} {per:%Y-%m}"
                        obj.save()
                        actualizadas.append(obj.id)
                    else:
                        omitidas.append(obj.id)

            return ok(
                message=f"Expensas generadas para {per:%Y-%m}. Creadas: {len(creadas)}, actualizadas: {len(actualizadas)}, omitidas: {len(omitidas)}",
                values={"creadas": creadas, "actualizadas": actualizadas, "omitidas": omitidas},
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            return fail(f"Error al generar expensas: {e}", status_code=status.HTTP_400_BAD_REQUEST)


# =============== Listados y consultas (Admin/Staff; Copropietario: sólo lo suyo) ===============
class ExpensasList(generics.ListAPIView):
    """
    Admin/Guardia/Empleado: ven todo; Copropietario: sólo su(s) unidad(es).
    Filtros: ?periodo=YYYY-MM (prefijo), ?unidad=<id>, ?estado=PENDIENTE/PARCIAL/PAGADA/ANULADA
    """
    serializer_class = ExpensaSerializer
    permission_classes = [permissions.IsAuthenticated, AdminOrStaffReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["unidad", "estado"]
    ordering_fields = ["periodo", "unidad", "estado", "saldo", "created_at"]

    def get_queryset(self):
        qs = Expensa.objects.select_related("unidad").all()
        role = _rol_name(self.request.user)
        if role == "Copropietario":
            unidad_ids = CopropietarioModel.objects.filter(idUsuario=self.request.user).values_list("unidad_id", flat=True)
            qs = qs.filter(unidad_id__in=unidad_ids)
        # filtro periodo: YYYY-MM
        periodo = self.request.query_params.get("periodo")
        if periodo:
            # filtra por mes (prefijo)
            qs = qs.filter(periodo__year=int(periodo.split("-")[0]), periodo__month=int(periodo.split("-")[1]))
        return qs.order_by("-periodo", "unidad_id")


class MisExpensasList(generics.ListAPIView):
    """
    CU09: Copropietario ve sus expensas (solo sus unidades).
    """
    serializer_class = ExpensaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        unidad_ids = CopropietarioModel.objects.filter(idUsuario=u).values_list("unidad_id", flat=True)
        return Expensa.objects.filter(unidad_id__in=unidad_ids).order_by("-periodo")

    def list(self, request, *args, **kwargs):
        data = self.get_serializer(self.get_queryset(), many=True).data
        return ok(message=f"Se encontraron {len(data)} expensas", values=data)


# =============== CU07: Crear pago (copropietario) ===============
class CrearPagoView(generics.CreateAPIView):
    """
    Crea un Pago en estado PENDIENTE con comprobante (opcional).
    Valida que la expensa pertenezca a alguna unidad del usuario (si es Copropietario).
    Admin también podría crear pagos manuales si lo necesitas.
    """
    serializer_class = PagoCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        if not ser.is_valid():
            return fail("Datos inválidos para registrar el pago", values=ser.errors)

        # Validación de pertenencia
        user = request.user
        role = _rol_name(user)
        expensa = ser.validated_data["expensa"]
        if role == "Copropietario":
            unidad_ids = set(CopropietarioModel.objects.filter(idUsuario=user).values_list("unidad_id", flat=True))
            if expensa.unidad_id not in unidad_ids:
                raise PermissionDenied("No puedes pagar expensas de otra unidad.")

        self.perform_create(ser)
        headers = self.get_success_headers(ser.data)
        return ok("Pago registrado correctamente", values=ser.data, status_code=status.HTTP_201_CREATED)


# =============== CU08: Aprobar / Rechazar pago (Admin) ===============
class AprobarPago(APIView):
    permission_classes = [IsAdmin]
    def post(self, request, pk):
        try:
            p = Pago.objects.get(pk=pk)
        except Pago.DoesNotExist:
            return fail("Pago no existe.", status_code=status.HTTP_404_NOT_FOUND)
        if p.estado != "APROBADO":
            p.estado = "APROBADO"; p.save(update_fields=["estado"])
        return ok("Pago aprobado", values={"id": p.id, "estado": p.estado})

class RechazarPago(APIView):
    permission_classes = [IsAdmin]
    def post(self, request, pk):
        try:
            p = Pago.objects.get(pk=pk)
        except Pago.DoesNotExist:
            return fail("Pago no existe.", status_code=status.HTTP_404_NOT_FOUND)
        if p.estado != "RECHAZADO":
            p.estado = "RECHAZADO"; p.save(update_fields=["estado"])
        return ok("Pago rechazado", values={"id": p.id, "estado": p.estado})


# =============== CU09: Consultar pagos/estado e historial ===============
class PagosDeExpensaList(generics.ListAPIView):
    """
    Lista pagos de una expensa:
    - Admin/Guardia/Empleado: permitido
    - Copropietario: solo si la expensa es de su unidad
    """
    serializer_class = PagoListSerializer
    permission_classes = [permissions.IsAuthenticated, AdminOrStaffReadOnly]

    def get_queryset(self):
        expensa_id = self.kwargs["pk"]
        qs = Pago.objects.filter(expensa_id=expensa_id).select_related("usuario", "expensa__unidad")
        role = _rol_name(self.request.user)
        if role == "Copropietario":
            unidad_ids = CopropietarioModel.objects.filter(idUsuario=self.request.user).values_list("unidad_id", flat=True)
            qs = qs.filter(expensa__unidad_id__in=unidad_ids)
        return qs.order_by("-created_at")

    def list(self, request, *args, **kwargs):
        data = self.get_serializer(self.get_queryset(), many=True).data
        return ok(message=f"{len(data)} pagos encontrados", values=data)
