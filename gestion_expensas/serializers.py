from rest_framework import serializers
from .models import Expensa, Pago

class ExpensaSerializer(serializers.ModelSerializer):
    unidad_codigo = serializers.CharField(source="unidad.codigo", read_only=True)
    class Meta:
        model = Expensa
        fields = ["id","unidad","unidad_codigo","periodo","vencimiento",
                  "monto_total","saldo","estado","glosa","created_at","updated_at"]

class PagoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = ["id","expensa","monto_bs","metodo","referencia","comprobante","estado","created_at"]
        read_only_fields = ["estado","created_at"]
    def create(self, validated_data):
        validated_data["usuario"] = self.context["request"].user
        # Fuerza estado inicial PENDIENTE
        validated_data["estado"] = "PENDIENTE"
        return super().create(validated_data)

class PagoListSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source="usuario.username", read_only=True)
    expensa_periodo = serializers.DateField(source="expensa.periodo", read_only=True)
    unidad_codigo = serializers.CharField(source="expensa.unidad.codigo", read_only=True)
    class Meta:
        model = Pago
        fields = ["id","expensa","expensa_periodo","unidad_codigo","usuario","usuario_username",
                  "monto_bs","metodo","referencia","comprobante","estado","created_at"]
