from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q
from rest_framework import serializers
from django.db import IntegrityError 
from .models import AreaComun, Reserva, AutorizacionVisita, RegistroVisitaModel
from users.models import CopropietarioModel, GuardiaModel
import os, requests

# --------- ÁREAS COMUNES / RESERVAS ---------

class AreaComunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaComun
        fields = "__all__"


class ReservaSerializer(serializers.ModelSerializer):
    # Comprobante opcional; si el área requiere pago, se vuelve obligatorio
    imagen = serializers.ImageField(write_only=True, required=False)
    area_comun = serializers.PrimaryKeyRelatedField(queryset=AreaComun.objects.all())

    class Meta:
        model = Reserva
        fields = "__all__"
        read_only_fields = ["usuario", "url_comprobante", "inicio", "fin"]

    def validate(self, data):
        fecha = data.get("fecha")
        hi    = data.get("hora_inicio")
        hf    = data.get("hora_fin")
        area  = data.get("area_comun")

        if not (fecha and hi and hf and area):
            raise serializers.ValidationError("fecha, hora_inicio, hora_fin y area_comun son obligatorios.")

        tz = timezone.get_current_timezone()
        inicio_dt = timezone.make_aware(datetime.combine(fecha, hi), tz)
        fin_dt    = timezone.make_aware(datetime.combine(fecha, hf), tz)

        # fin > inicio
        if fin_dt <= inicio_dt:
            raise serializers.ValidationError("La hora de fin debe ser posterior a la de inicio.")

        # Antelación 24h
        if inicio_dt < timezone.localtime() + timedelta(hours=24):
            raise serializers.ValidationError("Las reservas deben realizarse al menos 24 horas antes.")

        # Dentro del horario del área
        apertura = timezone.make_aware(datetime.combine(fecha, area.apertura_hora), tz)
        cierre   = timezone.make_aware(datetime.combine(fecha, area.cierre_hora), tz)
        if not (apertura <= inicio_dt and fin_dt <= cierre):
            raise serializers.ValidationError("La reserva debe estar dentro del horario del área.")

        # Antisolape lógico (mismo día/área). Permite back-to-back.
        solapa = (
            Reserva.objects
            .filter(area_comun=area, fecha=fecha, estado__in=["pendiente", "confirmada"])
            .filter(Q(hora_inicio__lt=hf) & Q(hora_fin__gt=hi))
            .exists()
        )
        if solapa:
            raise serializers.ValidationError("Ya existe una reserva en ese horario para esta área.")

        # Si el área requiere pago, exigir imagen en el request
        if area.requiere_pago and not self.initial_data.get("imagen"):
            raise serializers.ValidationError("Debe adjuntar comprobante (imagen) para esta área.")

        # Guardar los calculados para usarlos en create()
        data["inicio"] = inicio_dt
        data["fin"]    = fin_dt
        return data

    def create(self, validated_data):
        imagen = validated_data.pop("imagen", None)
        area   = validated_data["area_comun"]

        # Usuario = copropietario logueado
        user = self.context["request"].user
        try:
            copro = CopropietarioModel.objects.get(idUsuario=user)
        except CopropietarioModel.DoesNotExist:
            raise serializers.ValidationError("El usuario logueado no es un copropietario.")

        # Subir comprobante si el área lo requiere (o si se envió)
        if area.requiere_pago:
            if imagen is None:
                raise serializers.ValidationError("Debe adjuntar comprobante (imagen) para esta área.")
            api_key = os.getenv("IMGBB_API_KEY", "")
            if not api_key:
                raise serializers.ValidationError("Falta IMGBB_API_KEY en el servidor.")
            try:
                files = {"image": imagen.read()}
                resp = requests.post(f"https://api.imgbb.com/1/upload?key={api_key}", files=files, timeout=20)
                resp.raise_for_status()
                validated_data["url_comprobante"] = resp.json()["data"]["url"]
            except Exception:
                raise serializers.ValidationError("Error subiendo el comprobante.")

        # Create con manejo de ExclusionConstraint (anti-solape en DB)
        try:
            return Reserva.objects.create(usuario=copro, **validated_data)
        except IntegrityError:
            # Si otro proceso creó una reserva en el mismo intervalo justo ahora
            raise serializers.ValidationError("El horario se ocupó mientras confirmabas. Intenta con otro rango.")


# --------- VISITAS (CU11) ---------

class ListaVisitantesSerializer(serializers.ModelSerializer):
    copropietario = serializers.SerializerMethodField()
    nombre = serializers.CharField(source="visitante.nombre", read_only=True)
    apellido = serializers.CharField(source="visitante.apellido", read_only=True)
    documento = serializers.CharField(source="visitante.documento", read_only=True)  # OJO: tu modelo usa 'documento'

    class Meta:
        model = AutorizacionVisita
        fields = [
            "id",
            "copropietario",
            "nombre",
            "apellido",
            "documento",
            "motivo_visita",
            "hora_inicio",
            "hora_fin",
            "estado",
        ]

    def get_copropietario(self, obj):
        try:
            return obj.copropietario.idUsuario.username
        except Exception:
            return str(obj.copropietario_id)


class MarcarEntradaSerializer(serializers.Serializer):
    guardia_id = serializers.IntegerField()
    autorizacion_id = serializers.IntegerField()

    def validate(self, data):
        auth = AutorizacionVisita.objects.filter(pk=data["autorizacion_id"]).first()
        if not auth:
            raise serializers.ValidationError("Autorización no encontrada.")
        if auth.estado != "pendiente":
            raise serializers.ValidationError("La autorización no está pendiente.")

        guardia = GuardiaModel.objects.filter(idUsuario=data["guardia_id"]).first()
        if not guardia:
            raise serializers.ValidationError("Guardia no válido.")

        data["autorizacion"] = auth
        data["guardia"] = guardia
        return data

    def save(self):
        auth = self.validated_data["autorizacion"]
        guardia = self.validated_data["guardia"]
        registro = RegistroVisitaModel.objects.create(autorizacion=auth, guardia=guardia)
        auth.estado = "en visita"
        auth.save(update_fields=["estado"])
        return {"registro": registro, "autorizacion": auth}


class MarcarSalidaSerializer(serializers.Serializer):
    autorizacion_id = serializers.IntegerField()

    def validate(self, data):
        auth = AutorizacionVisita.objects.filter(pk=data["autorizacion_id"]).first()
        if not auth:
            raise serializers.ValidationError("Autorización no encontrada.")

        reg = (
            RegistroVisitaModel.objects.filter(autorizacion=auth, fecha_salida__isnull=True)
            .order_by("-id")
            .first()
        )
        if not reg:
            raise serializers.ValidationError("No hay visita en curso para esta autorización.")

        data["autorizacion"] = auth
        data["registro"] = reg
        return data

    def save(self):
        reg = self.validated_data["registro"]
        auth = self.validated_data["autorizacion"]
        reg.fecha_salida = timezone.now()
        reg.save(update_fields=["fecha_salida"])
        auth.estado = "completada"
        auth.save(update_fields=["estado"])
        return {"registro": reg, "autorizacion": auth}
