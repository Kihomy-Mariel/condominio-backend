from rest_framework import serializers
from django.utils import timezone
from .models import Comunicado

class ListarComunicadoSerializer(serializers.ModelSerializer):
    administrador = serializers.SerializerMethodField()

    class Meta:
        model = Comunicado
        fields = [
            "id",
            "titulo",
            "descripcion",
            "fecha_publicacion",
            "fecha_vencimiento",
            "tipo",
            "administrador",
            "activo",
            "imagen_url",
        ]

    def get_administrador(self, obj):
        # Muestra username del admin
        try:
            return obj.administrador.username
        except Exception:
            return obj.administrador_id


class ComunicadoSerializer(serializers.ModelSerializer):
    # El administrador lo ponemos automáticamente desde request.user; que no lo mande el cliente
    administrador = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Comunicado
        fields = [
            "id",
            "titulo",
            "descripcion",
            "imagen_url",
            "fecha_vencimiento",
            "tipo",
            "administrador",
            "activo",
            "fecha_publicacion",
        ]
        read_only_fields = ["administrador", "fecha_publicacion"]

    def validate(self, attrs):
        # Si envían fecha_vencimiento, que no sea antes de hoy (opcional, ajusta según tu regla)
        fv = attrs.get("fecha_vencimiento", None)
        if fv and fv < timezone.localdate():
            raise serializers.ValidationError("La fecha de vencimiento no puede ser anterior a hoy.")
        return attrs

    def create(self, validated_data):
        # Seteamos automáticamente el administrador desde el request
        request = self.context.get("request")
        validated_data["administrador"] = request.user
        return super().create(validated_data)
