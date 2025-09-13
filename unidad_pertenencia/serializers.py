from rest_framework import serializers
from .models import Unidad, Vehiculo, Mascota

class UnidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unidad
        fields = '__all__'
        read_only_fields = ["id", "created_at", "updated_at"]
        
    def validate_codigo(self, value):
            """"Validar que el codigo no este vacio y este en mayusculas"""
            if not value or len(value.strip()) == 0:
                raise serializers.ValidationError("El codigo es obligatorio.")
            return value.strip().upper()
        
    def validate_area_m2(self, value):
            """
            Validar que el area sea un valor positivo
            """ 
            
            if value <= 0:
                raise serializers.ValidationError("El area debe ser un valor positivo.")
            return value
    def validate_bloque(self, value):
            """"Validar que el bloque no este vacio"""
            if not value or len(value.strip()) == 0:
                raise serializers.ValidationError("El bloque es obligatorio.")
            return value.strip().upper()
    def validate_piso(self, value):
         """Validar que el piso sea un valor valido"""
         if value is None: 
                raise serializers.ValidationError("El piso es obligatorio.")
         if value < 0:
                raise serializers.ValidationError("El piso no puede ser negativo.")
         return value

    
class VehiculoSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Vehiculo
        fields = '__all__'
        read_only_fields = ["id", "created_at", "updated_at"]


    
    def validate_placa(self, value):
        """"Validar que la placa no este vacia y este en mayusculas"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("La placa es obligatoria.")
        value = value.upper().strip()
        if len(value) < 3 or len(value) > 10:
            raise serializers.ValidationError(
                "La placa debe tener entre 3 y 10 caracteres.")
        return value
        
    def validate_tag_codigo(self, value):
        """"Validar que el tag_codigo no este vacio"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("El tag_codigo es obligatorio.")
        value = value.strip()

        if len(value) < 4:
            raise serializers.ValidationError(
                 "El codigo del tag debe tener al menos 4 caracteres."
                 )
        return value
    
    def validate_unidad(self, value):
        """Validar que la unidad exista"""
        if not value:
            raise serializers.ValidationError("La unidad es obligatoria.")
        
        if value.estado != "activa":
            raise serializers.ValidationError("La unidad debe estar activa.")
        return value 
    
class MascotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mascota
        fields = '__all__'
        read_only_fields = ["id", "created_at", "updated_at"]
        
    def validate_nombre(self, value):
            """"Validar que el nombre no este vacio"""
            if not value or len(value.strip()) == 0:
                raise serializers.ValidationError("El nombre es obligatorio.")
            return value.strip()
        
    def validate_tipo_mascota(self, value):
            """"Validar que el tipo de animal no este vacio"""
            if not value or len(value.strip()) == 0:
                raise serializers.ValidationError("El tipo de animal es obligatorio.")
            return value.strip().lower()
    
    def validate_peso_kg(self, value):
            """
            Validar que el peso sea un valor positivo
            """ 
            
            if value is not None and value <= 0:
                raise serializers.ValidationError("El peso debe ser un valor positivo.")
            return value
    