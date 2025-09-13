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
        fields = ["id","expensa","monto_bs","metodo","referencia","comprobante","estado"]
        read_only_fields = ["estado"]
    def create(self, validated_data):
        validated_data["usuario"] = self.context["request"].user
        return super().create(validated_data)
