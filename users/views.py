# users/views.py
from rest_framework import generics, viewsets, status, filters
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import AuthenticationFailed
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import (
    UserSerializer,
    MyTokenObtainPairSerializer,
    CopropietarioSerializer,
    GuardiaSerializer,
    RolSerializer,
)
from .models import Usuario, Rol
from .permissions import IsAdminRole  # <- permiso por rol (Administrador)

User = get_user_model()


# ---------- REGISTROS ESPECÍFICOS (ADMIN-ONLY) ----------
class RegisterCopropietarioView(generics.CreateAPIView):
    serializer_class = CopropietarioSerializer
    permission_classes = [IsAdminRole]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        try:
            rol = Rol.objects.get(name='Copropietario')
            data['idRol'] = rol.idRol
        except Rol.DoesNotExist:
            return Response({
                "status": 2,
                "error": 1,
                "message": "El rol 'Copropietario' no existe. Ejecuta la siembra de roles."
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": 1,
                "error": 0,
                "message": "Usuario copropietario registrado correctamente",
                "values": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": 2,
            "error": 1,
            "message": "Usuario no se pudo registrar",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class RegisterGuardiaView(generics.CreateAPIView):
    serializer_class = GuardiaSerializer
    permission_classes = [IsAdminRole]   # <- solo Admin

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        try:
            rol = Rol.objects.get(name='Guardia')
            data['idRol'] = rol.idRol
        except Rol.DoesNotExist:
            return Response({
                "status": 2,
                "error": 1,
                "message": "El rol 'Guardia' no existe. Ejecuta la siembra de roles."
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": 1, "error": 0,
                "message": "Guardia registrado correctamente",
                "values": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": 2, "error": 1,
            "message": "No se pudo registrar guardia",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(generics.CreateAPIView):
    """
    Registro genérico de usuario (admin-only). Úsalo para crear administradores o empleados.
    Si no envías 'idRol' en el body, el serializer aplicará su default.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "status": 1,
            "error": 0,
            "message": "Usuario registrado correctamente",
            "values": serializer.data
        }, status=status.HTTP_201_CREATED)


# ---------- CRUD DE USUARIOS (ADMIN-ONLY) ----------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-id')
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]  # <- TODO el CRUD sólo para Admin
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'telefono', 'ci', 'idRol__name']
    filterset_fields = ['estado', 'idRol']
    ordering_fields = ['id', 'username', 'email', 'created_at']

    def list(self, request, *args, **kwargs):
        resp = super().list(request, *args, **kwargs)
        return Response({"status": 1, "error": 0, "message": "Usuarios listados correctamente", "values": resp.data})

    def retrieve(self, request, *args, **kwargs):
        resp = super().retrieve(request, *args, **kwargs)
        return Response({"status": 1, "error": 0, "message": "Usuario obtenido", "values": resp.data})

    def create(self, request, *args, **kwargs):
        resp = super().create(request, *args, **kwargs)
        return Response({"status": 1, "error": 0, "message": "Usuario creado", "values": resp.data}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        resp = super().update(request, *args, **kwargs)
        return Response({"status": 1, "error": 0, "message": "Usuario actualizado", "values": resp.data})

    def partial_update(self, request, *args, **kwargs):
        resp = super().partial_update(request, *args, **kwargs)
        return Response({"status": 1, "error": 0, "message": "Usuario actualizado", "values": resp.data})

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({"status": 1, "error": 0, "message": "Usuario eliminado"})


# ---------- AUTH ----------
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        print("Request data", request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed as e:
            error_msg = str(e)
            if "No active account" in error_msg:
                return Response({
                    "status": 2,
                    "error": 1,
                    "message": "Usuario o contraseña incorrectos"
                }, status=status.HTTP_401_UNAUTHORIZED)

            return Response({
                "status": 2,
                "error": 1,
                "message": error_msg
            }, status=status.HTTP_401_UNAUTHORIZED)

        return Response({
            "status": 1,
            "error": 0,
            "message": "Se inició sesión correctamente",
            "values": serializer.validated_data
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return Response({
                    "status": 2,
                    "error": 1,
                    "message": "No se proporcionó token de acceso"
                }, status=status.HTTP_400_BAD_REQUEST)

            token_str = auth_header.split(" ")[1]  # "Bearer <token>"
            token = AccessToken(token_str)

            # Si usas blacklist:
            if hasattr(token, 'blacklist'):
                token.blacklist()

            return Response({
                "status": 1,
                "error": 0,
                "message": "Se cerró la sesión correctamente",
            }, status=status.HTTP_205_RESET_CONTENT)

        except Exception as e:
            return Response({
                "status": 2,
                "error": 1,
                "message": f"Error al cerrar la sesión: {str(e)}",
            }, status=status.HTTP_400_BAD_REQUEST)


# ---------- PERFIL & ROLES ----------
class PerfilUsuarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user
        print(usuario.idRol)
        return Response({
            "status": 1,
            "error": 0,
            "message": "Perfil obtenido correctamente",
            "values": {
                "id": usuario.id,
                "username": usuario.username,
                "nombre": usuario.nombre,
                "last_name": usuario.last_name,
                "ci": usuario.ci,
                "email": usuario.email,
                "telefono": usuario.telefono,
                "rol": getattr(getattr(usuario, 'idRol', None), 'name', None),
            }
        }, status=status.HTTP_200_OK)


class RolesListView(generics.ListAPIView):
    queryset = Rol.objects.all().order_by('idRol')
    serializer_class = RolSerializer
    permission_classes = [IsAdminRole]  # ← sólo Admin los consulta (para el select del formulario)
