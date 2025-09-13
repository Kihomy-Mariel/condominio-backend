from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from .models import Unidad, Vehiculo, Mascota
from .serializers import UnidadSerializer, VehiculoSerializer, MascotaSerializer

# Create your views here.
import logging  # para registrar errores en el servidor

logger = logging.getLogger(__name__)


@api_view(["POST"])
# @permission_classes([IsAuthenticated]) #temporal, cambiar cuando este la auth
@permission_classes([])
def crearUnidad(request):
    """CU03 - Crear nueva unidad
    Solo administradores pueden crear unidades"""
    try:
        # TODO: Validar que el usuario sea administrador cuando esté listo el sistema de auth
        # if request.user.rol != 'administrador':
        #     return Response({
        #         'status': 2,
        #         'error': 1,
        #         'message': 'No tiene permisos para crear unidades',
        #         'data': None
        #     }, status=status.HTTP_403_FORBIDDEN)
        serializer = UnidadSerializer(data=request.data)
        if serializer.is_valid():
            # validar unicidad del codigo
            codigo = serializer.validated_data.get("codigo")

            if Unidad.objects.filter(codigo=codigo).exists():
                return Response(
                    {
                        "status": 2,
                        "error": 1,
                        "message": "Ya existe una unidad con ese codigo",
                        "data": None,
                    }
                )
            unidad = serializer.save()  # crea en la bd

            return Response(
                {
                    "status": 1,
                    "error": 0,
                    "message": f"Unidad {unidad.codigo} creada exitosamente",
                    "data": UnidadSerializer(unidad).data,
                    # ['id',
                    # 'codigo',
                    #  'bloque',
                    # 'piso',
                    # 'numero',
                    # 'area_m2',
                    # 'estado',
                    # tipo_unidad
                    # 'created_at', 'updated_at']
                    # devuelve todo lo que esta en fields del serializador
                }
            )
        else:
            return Response(
                {
                    "status": 2,
                    "error": 1,
                    "message": "Datos invalidos para crear la unidad",
                    "values": serializer.errors,
                }
            )
    except Exception as e:
        logger.error(f"Error al crear unidad: {str(e)}")
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "Error interno del servidor al crear la unidad",
                "values": None,
            }
        )


@api_view(["PUT"])
# @permission_classes([IsAuthenticated]) #temporal, cambiar cuando este la auth
@permission_classes([])
def editar_unidad(request, unidad_id):
    """CU04 - Editar unidad existente
    Solo administradores pueden editar unidades, no edita id"""
    try:
        # TODO: Validar permisos de administrador
        unidad = Unidad.objects.get(id=unidad_id)
        # Validar que el codigo no este duplicado(excluyendo la unidad actual)
        codigo = request.data.get("codigo")

        if (
            codigo
            and Unidad.objects.filter(codigo=codigo).exclude(id=unidad_id).exists()
        ):
            return Response(
                {
                    "status": 2,
                    "error": 1,
                    "message": "Ya existe una unidad con ese codigo",
                    "values": None,
                }
            )
        serializer = UnidadSerializer(unidad, data=request.data, partial=True)
        # partial permite actualizaciones parciales, de algunos campos

        if serializer.is_valid():
            unidad_actualizada = serializer.save()
            return Response(
                {
                    "status": 1,
                    "error": 0,
                    "message": f"Unidad {unidad_actualizada.codigo} actualizada exitosamente",
                    "values": UnidadSerializer(unidad_actualizada).data,
                    # ['id',
                    # 'codigo',
                    # 'bloque',
                    # 'piso',
                    #  'numero',
                    #  'area_m2',
                    # 'estado',
                    # tipo_unidad
                    # 'created_at', 'updated_at']
                    # devuelve todo lo que esta en fields del serializador
                }
            )
        else:
            return Response(
                {
                    "status": 2,
                    "error": 1,
                    "message": "Datos invalidos para actualizar la unidad",
                    "values": serializer.errors,
                }
            )
    except Unidad.DoesNotExist:
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "La unidad no encontrada",
                "values": None,
            }
        )
    except Exception as e:
        logger.error(f"Error al editar unidad:{unidad_id}: {str(e)}")
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "Error interno del servidor al editar la unidad",
                "values": None,
            }
        )


@api_view(["PATCH"])
@permission_classes([])  # temporal, cambiar cuando este la auth
def cambiar_estado_unidad(request, unidad_id):
    """CU05 - Cambiar estado de una unidad (activa/inactiva)
    Solo administradores pueden cambiar el estado de las unidades"""
    try:
        # TODO: Validar permisos de administrador
        unidad = Unidad.objects.get(id=unidad_id)
        nuevo_estado = request.data.get("estado")

        if nuevo_estado not in ["activa", "inactiva", "mantenimiento"]:
            return Response(
                {
                    "status": 2,
                    "error": 1,
                    "message": 'Estado invalido. Debe ser "activa", "inactiva" o "mantenimiento"',
                    "values": None,
                }
            )
        estado_anterior = unidad.estado
        unidad.estado = nuevo_estado
        unidad.save()

        return Response(
            {
                "status": 1,
                "error": 0,
                "message": f"Estado de la unidad {unidad.codigo} cambiado de {estado_anterior} a {nuevo_estado} exitosamente",
                "values": {
                    "id_unidad": unidad.id,
                    "codigo": unidad.codigo,
                    "estado_anterior": estado_anterior,
                    "estado_actual": nuevo_estado,
                },
            }
        )
    except Unidad.DoesNotExist:
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "La unidad no encontrada",
                "values": None,
            }
        )
    except Exception as e:
        logger.error(f"Error al cambiar estado de la unidad {unidad_id}: {str(e)}")
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "Error interno del servidor al cambiar el estado de la unidad",
                "values": None,
            }
        )


@api_view(["GET"])
@permission_classes([])  # temporal, cambiar cuando este la auth
def listar_unidades(request):
    """CU03 - Listar todas las unidades con sus detalles"""
    try:
        # TODO: Validar permisos de administrador o copropietario
        unidades = Unidad.objects.all().order_by("bloque", "piso", "numero")

        # Usar el serializer para convertir los objetos
        serializer = UnidadSerializer(unidades, many=True)
        return Response(
            {
                "status": 1,
                "error": 0,
                "message": f"Se encontraron {len(unidades)} unidades",
                "values": serializer.data,
                # ['id',
                #  'codigo',
                #  'bloque',
                # 'piso',
                # 'numero',
                # 'area_m2',
                # 'estado',
                #  tipo_unidad
                # 'created_at', 'updated_at']
                # devuelve todo lo que esta en fields del serializador
            }
        )
    except Exception as e:
        logger.error(f"Error al listar unidades: {str(e)}")
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "Error interno del servidor al listar las unidades",
                "values": None,
            }
        )


@api_view(["GET"])
@permission_classes([])  # temporal, cambiar cuando este la auth
def obtener_unidad(request, unidad_id):
    """CU03 - Obtener detalles de una unidad por su ID"""
    try:
        unidad = Unidad.objects.get(id=unidad_id)
        serializer = UnidadSerializer(unidad)
        return Response(
            {
                "status": 1,
                "error": 0,
                "message": f"Detalles de la unidad {unidad.codigo} obtenidos exitosamente",
                "values": serializer.data,
                # ['id',
                # 'codigo',
                #  'bloque',
                # 'piso',
                # 'numero',
                #  'area_m2',
                # 'estado',
                # tipo_unidad
                # 'created_at', 'updated_at']
                # devuelve todo lo que esta en fields del serializador
            }
        )

    except Unidad.DoesNotExist:
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "La unidad no encontrada",
                "values": None,
            }
        )
    except Exception as e:
        logger.error(f"Error al obtener unidad {unidad_id}: {str(e)}")
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "Error interno del servidor al obtener los detalles de la unidad",
                "values": None,
            }
        )


@api_view(["POST"])
@permission_classes([])
def registrar_vehiculo(request):
    """CU05 - Registrar vehículo con tag de acceso
    Los copropietarios pueden registrar vehículos para sus unidades
    campos obligatorios a mandar: placa, marca, modelo, tag_codigo, unidad_id
    El tipo_vehiculo debe pertenecer al conjunto definido en el modelo
    mandar id de la unidad ACTIVA"""
    try:
        serializer = VehiculoSerializer(data=request.data)

        if serializer.is_valid():
            # Validar unicidad de placa
            placa = serializer.validated_data.get("placa")
            if Vehiculo.objects.filter(placa=placa).exists():
                return Response(
                    {
                        "status": 2,
                        "error": 1,
                        "message": "Ya existe un vehículo registrado con esa placa",
                        "values": None,
                    }
                )

            # Validar unicidad de tag_codigo
            tag_codigo = serializer.validated_data.get("tag_codigo")
            if Vehiculo.objects.filter(tag_codigo=tag_codigo).exists():
                return Response(
                    {
                        "status": 2,
                        "error": 1,
                        "message": "Ya existe un vehículo registrado con ese código de tag",
                        "values": None,
                    }
                )

            vehiculo = serializer.save()

            return Response(
                {
                    "status": 1,
                    "error": 0,
                    "message": f"Vehículo {vehiculo.placa} registrado exitosamente con tag {vehiculo.tag_codigo}",
                    "values": VehiculoSerializer(vehiculo).data,
                }
            )
        else:
            return Response(
                {
                    "status": 2,
                    "error": 1,
                    "message": "Datos inválidos para registrar el vehículo",
                    "values": serializer.errors,
                }
            )

    except Exception as e:
        logger.error(f"Error al registrar vehículo: {str(e)}")
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "Error interno del servidor al registrar el vehículo",
                "values": None,
            }
        )


@api_view(["PUT"])
@permission_classes([])
def editar_vehiculo(request, vehiculo_id):
    """
    Editar vehículo existente
    El tipo_vehiculo debe pertenecer al conjunto definido en el modelo
    """

    try:
        vehiculo = Vehiculo.objects.get(id=vehiculo_id)

        # Validar unicidad de placa (excluyendo el vehículo actual)
        placa = request.data.get("placa")
        if (
            placa
            and Vehiculo.objects.filter(placa=placa).exclude(id=vehiculo_id).exists()
        ):
            return Response(
                {
                    "status": 2,
                    "error": 1,
                    "message": "Ya existe un vehículo con esa placa",
                    "values": None,
                }
            )

        # Validar unicidad de tag_codigo (excluyendo el vehículo actual)
        tag_codigo = request.data.get("tag_codigo")
        if (
            tag_codigo
            and Vehiculo.objects.filter(tag_codigo=tag_codigo)
            .exclude(id=vehiculo_id)
            .exists()
        ):
            return Response(
                {
                    "status": 2,
                    "error": 1,
                    "message": "Ya existe un vehículo con ese código de tag",
                    "values": None,
                }
            )

        serializer = VehiculoSerializer(vehiculo, data=request.data, partial=True)

        if serializer.is_valid():
            vehiculo_actualizado = serializer.save()
            return Response(
                {
                    "status": 1,
                    "error": 0,
                    "message": f"Vehículo {vehiculo_actualizado.placa} actualizado exitosamente",
                    "values": VehiculoSerializer(vehiculo_actualizado).data,
                }
            )
        else:
            return Response(
                {
                    "status": 2,
                    "error": 1,
                    "message": "Datos inválidos para actualizar el vehículo",
                    "values": serializer.errors,
                }
            )

    except Vehiculo.DoesNotExist:
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "El vehículo no fue encontrado",
                "values": None,
            }
        )
    except Exception as e:
        logger.error(f"Error al editar vehículo {vehiculo_id}: {str(e)}")
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "Error interno del servidor al editar el vehículo",
                "values": None,
            }
        )


@api_view(["PATCH"])
@permission_classes([])
def cambiar_estado_vehiculo(request, vehiculo_id):
    """Cambiar estado de un vehículo (activo/inactivo/bloqueado)"""
    try:
        vehiculo = Vehiculo.objects.get(id=vehiculo_id)

        nuevo_estado = request.data.get("estado")
        if nuevo_estado not in ["activo", "inactivo", "bloqueado"]:
            return Response(
                {
                    "status": 2,
                    "error": 1,
                    "message": 'Estado inválido. Debe ser "activo", "inactivo" o "bloqueado"',
                    "values": None,
                }
            )

        estado_anterior = vehiculo.estado
        vehiculo.estado = nuevo_estado
        vehiculo.save()

        return Response(
            {
                "status": 1,
                "error": 0,
                "message": f"Estado del vehículo {vehiculo.placa} cambiado de {estado_anterior} a {nuevo_estado} exitosamente",
                "values": {
                    "id_vehiculo": vehiculo.id,
                    "placa": vehiculo.placa,
                    "tag_codigo": vehiculo.tag_codigo,
                    "estado_anterior": estado_anterior,
                    "estado_actual": nuevo_estado,
                },
            }
        )

    except Vehiculo.DoesNotExist:
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "El vehículo no fue encontrado",
                "values": None,
            }
        )
    except Exception as e:
        logger.error(f"Error al cambiar estado del vehículo {vehiculo_id}: {str(e)}")
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "Error interno del servidor al cambiar el estado del vehículo",
                "values": None,
            }
        )


@api_view(["PATCH"])
@permission_classes([])
def bloquear_acceso_vehiculo(request, vehiculo_id):
    """Bloquear/desbloquear acceso de un vehículo"""
    try:
        vehiculo = Vehiculo.objects.get(id=vehiculo_id)

        acceso_bloqueado = request.data.get("acceso_bloqueado", False)

        estado_anterior = vehiculo.acceso_bloqueado
        vehiculo.acceso_bloqueado = acceso_bloqueado
        vehiculo.save()

        accion = "bloqueado" if acceso_bloqueado else "desbloqueado"

        return Response(
            {
                "status": 1,
                "error": 0,
                "message": f"Acceso del vehículo {vehiculo.placa} {accion} exitosamente",
                "values": {
                    "id_vehiculo": vehiculo.id,
                    "placa": vehiculo.placa,
                    "tag_codigo": vehiculo.tag_codigo,
                    "acceso_anterior": estado_anterior,
                    "acceso_actual": acceso_bloqueado,
                },
            }
        )

    except Vehiculo.DoesNotExist:
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "El vehículo no fue encontrado",
                "values": None,
            }
        )
    except Exception as e:
        logger.error(f"Error al bloquear/desbloquear vehículo {vehiculo_id}: {str(e)}")
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "Error interno del servidor al cambiar el acceso del vehículo",
                "values": None,
            }
        )


@api_view(["GET"])
@permission_classes([])
def listar_vehiculos(request):
    """Listar todos los vehículos o por unidad"""
    try:
        unidad_id = request.query_params.get("unidad_id", None)

        if unidad_id:
            vehiculos = Vehiculo.objects.filter(unidad_id=unidad_id).order_by("placa")
        else:
            vehiculos = Vehiculo.objects.all().order_by("placa")

        serializer = VehiculoSerializer(vehiculos, many=True)
        return Response(
            {
                "status": 1,
                "error": 0,
                "message": f"Se encontraron {len(vehiculos)} vehículos",
                "values": serializer.data,
            }
        )

    except Exception as e:
        logger.error(f"Error al listar vehículos: {str(e)}")
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "Error interno del servidor al listar los vehículos",
                "values": None,
            }
        )


@api_view(["GET"])
@permission_classes([])
def obtener_vehiculo(request, vehiculo_id):
    """Obtener detalles de un vehículo por su ID"""
    try:
        vehiculo = Vehiculo.objects.get(id=vehiculo_id)

        serializer = VehiculoSerializer(vehiculo)
        return Response(
            {
                "status": 1,
                "error": 0,
                "message": f"Detalles del vehículo {vehiculo.placa} obtenidos exitosamente",
                "values": serializer.data,
            }
        )

    except Vehiculo.DoesNotExist:
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "El vehículo no fue encontrado",
                "values": None,
            }
        )
    except Exception as e:
        logger.error(f"Error al obtener vehículo {vehiculo_id}: {str(e)}")
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "Error interno del servidor al obtener los detalles del vehículo",
                "values": None,
            }
        )


# ==================== VIEWS DE MASCOTAS ====================


@api_view(["POST"])
@permission_classes([])
def registrar_mascota(request):
    """Registrar nueva mascota
    campos obligatorios a mandar: nombre, unidad_id que tiene que tener de estado ACTIVA
    """
    try:
        serializer = MascotaSerializer(data=request.data)

        if serializer.is_valid():
            mascota = serializer.save()

            return Response(
                {
                    "status": 1,
                    "error": 0,
                    "message": f"Mascota {mascota.nombre} registrada exitosamente",
                    "values": MascotaSerializer(mascota).data,
                }
            )
        else:
            return Response(
                {
                    "status": 2,
                    "error": 1,
                    "message": "Datos inválidos para registrar la mascota",
                    "values": serializer.errors,
                }
            )

    except Exception as e:
        logger.error(f"Error al registrar mascota: {str(e)}")
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "Error interno del servidor al registrar la mascota",
                "values": None,
            }
        )


@api_view(["PUT"])
@permission_classes([])
def editar_mascota(request, mascota_id):
    """Editar mascota existente"""
    try:
        mascota = Mascota.objects.get(id=mascota_id)

        serializer = MascotaSerializer(mascota, data=request.data, partial=True)

        if serializer.is_valid():
            mascota_actualizada = serializer.save()
            return Response(
                {
                    "status": 1,
                    "error": 0,
                    "message": f"Mascota {mascota_actualizada.nombre} actualizada exitosamente",
                    "values": MascotaSerializer(mascota_actualizada).data,
                }
            )
        else:
            return Response(
                {
                    "status": 2,
                    "error": 1,
                    "message": "Datos inválidos para actualizar la mascota",
                    "values": serializer.errors,
                }
            )

    except Mascota.DoesNotExist:
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "La mascota no fue encontrada",
                "values": None,
            }
        )


@api_view(["PATCH"])
@permission_classes([])
def cambiar_estado_mascota(request, mascota_id):
    """
    Activar/desactivar una mascota

    """
    try:
        mascota = Mascota.objects.get(id=mascota_id)

        activo = request.data.get("activo")
        if activo is None:
            return Response(
                {
                    "status": 2,
                    "error": 1,
                    "message": "Debe especificar el estado activo (true/false)",
                    "values": None,
                }
            )

        estado_anterior = mascota.activo
        mascota.activo = activo
        mascota.save()

        accion = "activada" if activo else "desactivada"

        return Response(
            {
                "status": 1,
                "error": 0,
                "message": f"Mascota {mascota.nombre} {accion} exitosamente",
                "values": {
                    "id_mascota": mascota.id,
                    "nombre": mascota.nombre,
                    "estado_anterior": estado_anterior,
                    "estado_actual": activo,
                },
            }
        )

    except Mascota.DoesNotExist:
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "La mascota no fue encontrada",
                "values": None,
            }
        )


@api_view(["GET"])
@permission_classes([])
def listar_mascotas(request):
    """Listar todas las mascotas o por unidad"""
    try:
        unidad_id = request.query_params.get("unidad_id", None)
        tipo_mascota = request.query_params.get("tipo_mascota", None)

        mascotas = Mascota.objects.all()

        if unidad_id:
            mascotas = mascotas.filter(unidad_id=unidad_id)

        if tipo_mascota:
            mascotas = mascotas.filter(tipo_mascota=tipo_mascota)

        mascotas = mascotas.order_by("nombre")

        serializer = MascotaSerializer(mascotas, many=True)
        return Response(
            {
                "status": 1,
                "error": 0,
                "message": f"Se encontraron {len(mascotas)} mascotas",
                "values": serializer.data,
                # unidad
                # activo
                # acceso_bloqueado
                # created_at
                # updated_at
                # nombre
                # tipo_mascota
                # raza
                # color
                # peso_kg
            }
        )

    except Exception as e:
        logger.error(f"Error al listar mascotas: {str(e)}")
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "Error interno del servidor al listar las mascotas",
                "values": None,
            }
        )


@api_view(["GET"])
@permission_classes([])
def obtener_mascota(request, mascota_id):
    """Obtener detalles de una mascota por su ID"""
    try:
        mascota = Mascota.objects.get(id=mascota_id)

        serializer = MascotaSerializer(mascota)
        return Response(
            {
                "status": 1,
                "error": 0,
                "message": f"Detalles de la mascota {mascota.nombre} obtenidos exitosamente",
                "values": serializer.data,
                # Retorna: {
                #   'id': int,
                #   'nombre': str,
                #   'tipo_mascota': str ('perro', 'gato', 'ave', 'pez', 'otro'),
                #   'raza': str,
                #   'color': str,
                #   'peso_kg': decimal,
                #   'unidad': int (ID de la unidad),
                #   'activo': bool,
                #   'acceso_bloqueado': bool,
                #   'created_at': datetime,
                #   'updated_at': datetime
                # }
            }
        )

    except Mascota.DoesNotExist:
        return Response(
            {
                "status": 2,
                "error": 1,
                "message": "La mascota no fue encontrada",
                "values": None,
            }
        )
