from rest_framework import serializers
from .models import Comunicado


class ListarComunicadoSerializer(serializers.ModelSerializer):
    administrador = serializers.StringRelatedField()
    class Meta:
        model = Comunicado
        fields = [
            "titulo",
            "descripcion",
            "fecha_publicacion",
            "fecha_vencimiento",
            "tipo",
            "administrador",
            "activo",
            "imagen_url",
        ]
        read_only_fields = [
            "activo"
        ]  # si quieres que siempre se cree activo por default

class ComunicadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comunicado
        fields = [
            "titulo",
            "descripcion",
            "imagen_url",
            "fecha_vencimiento",
            "tipo",
            "administrador",
            "activo",
        ]
        read_only_fields = [
            "activo"
        ]  # si quieres que siempre se cree activo por default