# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import GuardiaModel, Usuario, CopropietarioModel, Rol

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    idRol = serializers.PrimaryKeyRelatedField(queryset=Rol.objects.all(), required=False)

    class Meta:
        model = User
        fields = ['id','username','nombre','last_name','ci','telefono','email','password','idRol']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        rol = validated_data.pop('idRol', None) or Rol.objects.get(name='Copropietario')  # o el que definas por defecto
        user = User(**validated_data, idRol=rol)
        if not password:
            raise serializers.ValidationError({"password": "La contraseña es obligatoria"})
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        rol_name = getattr(getattr(self.user, 'idRol', None), 'name', None)
        data['id'] = self.user.id
        data['username'] = self.user.username
        data['nombre'] = self.user.nombre  
        data['last_name'] = self.user.last_name
        data['email'] = self.user.email
        data['rol'] = rol_name
        data['is_staff'] = self.user.is_staff
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6, write_only=True)
    token = serializers.CharField(write_only=True)
    uidb64 = serializers.CharField(write_only=True)


# --- Registro de Copropietario ---
class CopropietarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    unidad = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Usuario
        fields = ['username','nombre','last_name','ci','email','telefono','password','idRol','unidad']
        extra_kwargs = {'idRol': {'required': False}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        unidad = validated_data.pop('unidad', None)
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()
        CopropietarioModel.objects.create(idUsuario=usuario, unidad=unidad or "")
        return usuario

# --- Registro de Guardia ---
class GuardiaSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    # válido y requerido para evitar errores en DB (turno es obligatorio en tu modelo)
    turno = serializers.ChoiceField(choices=['mañana', 'tarde', 'noche'], write_only=True, required=True)

    class Meta:
        model = Usuario
        fields = ['username', 'nombre', 'email', 'ci', 'telefono', 'password', 'idRol', 'turno']
        extra_kwargs = {'idRol': {'required': False}}  # lo fuerzas a 3 en la vista

    def create(self, validated_data):
        turno = validated_data.pop('turno')              # <- pop ANTES de crear el usuario
        password = validated_data.pop('password')
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()

        GuardiaModel.objects.create(idUsuario=usuario, turno=turno)
        return usuario


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['idRol', 'name']