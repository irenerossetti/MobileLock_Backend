import hashlib
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from apps.devices.models import Dispositivo, HistorialEscaneo, HistorialTrazabilidad
from apps.devices.serializers import (
    DispositivoSerializer,
    HistorialEscaneoSerializer,
    HistorialTrazabilidadSerializer,
)
from apps.devices.permissions import IsDeviceOwner
from apps.devices.services import DeviceService
from apps.users.models import puede_realizar_accion, Profile
from apps.saas.models import UsageLog


class DeviceListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        devices = DeviceService.get_user_devices(request.user)

        serializer = DispositivoSerializer(devices, many=True)

        return Response(serializer.data)

    def post(self, request):

        serializer = DispositivoSerializer(data=request.data)

        if serializer.is_valid():

            try:
                device = DeviceService.create_device(
                    request.user,
                    serializer.validated_data
                )
            except ValueError as exc:
                return Response(
                    {"detail": str(exc)},
                    status=status.HTTP_403_FORBIDDEN,
                )

            return Response(
                DispositivoSerializer(device).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeviceDetailView(APIView):

    permission_classes = [IsAuthenticated, IsDeviceOwner]

    def get_object(self, pk):
        return get_object_or_404(Dispositivo, id_dispositivo=pk)

    def get(self, request, pk):

        device = self.get_object(pk)

        self.check_object_permissions(request, device)

        serializer = DispositivoSerializer(device)

        return Response(serializer.data)

    def put(self, request, pk):

        device = self.get_object(pk)

        self.check_object_permissions(request, device)

        device = DeviceService.update_device(device, request.data)

        serializer = DispositivoSerializer(device)

        return Response(serializer.data)

    def delete(self, request, pk):

        device = self.get_object(pk)

        self.check_object_permissions(request, device)

        DeviceService.delete_device(device)

        return Response(status=status.HTTP_204_NO_CONTENT)


class DeviceVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        imei = request.query_params.get("imei")
        qr_code = request.query_params.get("qr_code")

        if not imei and not qr_code:
            return Response(
                {"detail": "Debes enviar imei o qr_code para la verificación."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Validar límite de verificaciones del plan
        if not puede_realizar_accion(request.user, "verificacion"):
            return Response(
                {"detail": "Límite mensual de verificaciones alcanzado para tu plan."},
                status=status.HTTP_403_FORBIDDEN
            )

        tipo_filtro = "IMEI" if imei else "QR"
        valor_buscado = imei or qr_code

        device = None
        # 2. Buscar dispositivo
        if imei:
            # Buscar directamente por el IMEI recibido
            device = Dispositivo.objects.filter(hash_imei=imei).first()
            if not device:
                # O hasheando por si se ingresó plano y se almacena hasheado
                imei_hash = hashlib.sha256(imei.encode("utf-8")).hexdigest()
                device = Dispositivo.objects.filter(hash_imei=imei_hash).first()
        elif qr_code:
            # Buscar por hardware hash o id
            device = Dispositivo.objects.filter(hash_adn_hardware=qr_code).first()
            if not device:
                if qr_code.isdigit():
                    device = Dispositivo.objects.filter(id_dispositivo=int(qr_code)).first()

        # 3. Determinar estado
        if device:
            resultado_estado = device.estado  # LIBRE o ROBADO
            marca_modelo = device.marca_modelo
        else:
            resultado_estado = "NO_REGISTRADO"
            marca_modelo = None

        # 4. Descontar uso del perfil e incrementar en UsageLog
        profile, _ = Profile.objects.get_or_create(usuario=request.user)
        profile.verificaciones_usadas_este_mes += 1
        profile.save(update_fields=["verificaciones_usadas_este_mes"])

        UsageLog.objects.create(
            usuario=request.user,
            tipo_accion=f"verificacion_{tipo_filtro.lower()}",
            dispositivo_id=str(device.id_dispositivo) if device else None
        )

        # 5. Guardar en el Historial de Escaneos local
        HistorialEscaneo.objects.create(
            usuario=request.user,
            tipo_filtro=tipo_filtro,
            valor_consultado=valor_buscado,
            resultado_estado=resultado_estado,
            marca_modelo_detectado=marca_modelo
        )

        # 6. Retornar respuesta
        payload = {
            "estado": resultado_estado,
            "valor_consultado": valor_buscado,
            "tipo_filtro": tipo_filtro,
            "mensaje": f"El dispositivo se encuentra {resultado_estado.lower()}." if device else "El dispositivo no está registrado en el sistema.",
        }
        if device:
            payload["dispositivo"] = DispositivoSerializer(device).data

        return Response(payload, status=status.HTTP_200_OK)

    def post(self, request):
        import os
        import json
        import tempfile
        import logging
        from apps.devices.ai_service import AIService

        logger = logging.getLogger(__name__)

        imei = request.data.get("imei") or request.query_params.get("imei")
        qr_code = request.data.get("qr_code") or request.query_params.get("qr_code")
        imagen_verificacion = request.FILES.get("imagen_verificacion")

        if not imei and not qr_code:
            return Response(
                {"detail": "Debes enviar imei o qr_code para la verificación."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not imagen_verificacion:
            return Response(
                {"detail": "Debes proporcionar el archivo de imagen 'imagen_verificacion' para la verificación física."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Validar límite de verificaciones del plan
        if not puede_realizar_accion(request.user, "verificacion"):
            return Response(
                {"detail": "Límite mensual de verificaciones alcanzado para tu plan."},
                status=status.HTTP_403_FORBIDDEN
            )

        tipo_filtro = "IMEI" if imei else "QR"
        valor_buscado = imei or qr_code

        device = None
        # 2. Buscar dispositivo
        if imei:
            device = Dispositivo.objects.filter(hash_imei=imei).first()
            if not device:
                imei_hash = hashlib.sha256(imei.encode("utf-8")).hexdigest()
                device = Dispositivo.objects.filter(hash_imei=imei_hash).first()
        elif qr_code:
            device = Dispositivo.objects.filter(hash_adn_hardware=qr_code).first()
            if not device:
                if qr_code.isdigit():
                    device = Dispositivo.objects.filter(id_dispositivo=int(qr_code)).first()

        if not device:
            return Response(
                {"detail": "El dispositivo consultado no está registrado en el sistema."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. Validar si el dispositivo cuenta con huella visual de referencia
        if not device.hash_visual or not device.vector_caracteristicas:
            return Response(
                {"detail": "El dispositivo consultado no cuenta con una huella visual de referencia registrada. No se puede realizar la comparación física."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Procesar imagen en vivo
        temp_path = None
        try:
            # Escribir el archivo subido en una ubicación temporal local
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                for chunk in imagen_verificacion.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name

            # Extraer vector de la imagen en vivo
            vector_live = AIService.extraer_vector_caracteristicas(temp_path)
            
            # Cargar vector de referencia
            vector_ref = json.loads(device.vector_caracteristicas)

            # Calcular Similitud Coseno
            similarity = AIService.calcular_similitud_coseno(vector_ref, vector_live)
            
            # Determinar autenticidad (umbral del 70%)
            autentico = similarity >= 0.70
            
        except Exception as e:
            logger.error(f"Error procesando verificación física con IA: {str(e)}", exc_info=True)
            return Response(
                {"detail": f"Ocurrió un error al analizar la imagen física: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Eliminar archivo temporal
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

        # 5. Descontar uso del perfil e incrementar en UsageLog
        profile, _ = Profile.objects.get_or_create(usuario=request.user)
        profile.verificaciones_usadas_este_mes += 1
        profile.save(update_fields=["verificaciones_usadas_este_mes"])

        UsageLog.objects.create(
            usuario=request.user,
            tipo_accion="verificacion_fisica",
            dispositivo_id=str(device.id_dispositivo)
        )

        # 6. Guardar en el Historial de Escaneos local
        HistorialEscaneo.objects.create(
            usuario=request.user,
            tipo_filtro=tipo_filtro,
            valor_consultado=valor_buscado,
            resultado_estado=device.estado,
            marca_modelo_detectado=device.marca_modelo
        )

        # 7. Retornar respuesta
        payload = {
            "autentico": autentico,
            "similitud": similarity,
            "umbral": 0.70,
            "mensaje": (
                f"El dispositivo físico coincide con el registro original (Similitud: {similarity * 100:.1f}%)."
                if autentico else
                f"Alerta de Autenticidad: El dispositivo físico NO coincide con el registro original (Similitud: {similarity * 100:.1f}%)."
            ),
            "url_imagen_referencia": request.build_absolute_uri(device.url_imagen_referencia.url) if device.url_imagen_referencia else None,
            "dispositivo": DispositivoSerializer(device).data
        }

        return Response(payload, status=status.HTTP_200_OK)


class HistorialEscaneoListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        historial = HistorialEscaneo.objects.filter(usuario=request.user)
        serializer = HistorialEscaneoSerializer(historial, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeviceTransferView(APIView):
    permission_classes = [IsAuthenticated, IsDeviceOwner]

    def post(self, request, pk):
        device = get_object_or_404(Dispositivo, id_dispositivo=pk)
        self.check_object_permissions(request, device)

        if device.estado != "LIBRE":
            return Response(
                {"detail": f"No puedes transferir un dispositivo en estado {device.estado}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        nuevo_propietario_email = request.data.get("nuevo_propietario_email")
        if not nuevo_propietario_email:
            return Response(
                {"detail": "Debes proporcionar el correo electrónico del nuevo propietario."},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.users.models import Usuario
        nuevo_propietario = Usuario.objects.filter(correo_electronico=nuevo_propietario_email).first()
        if not nuevo_propietario:
            return Response(
                {"detail": "El usuario destino no existe en el sistema."},
                status=status.HTTP_404_NOT_FOUND
            )

        if nuevo_propietario == request.user:
            return Response(
                {"detail": "No puedes transferir el dispositivo a ti mismo."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update ownership
        device.id_usuario_propietario = nuevo_propietario
        device.save()

        # Opcional: Registrar la transferencia en un historial si es necesario

        return Response(
            {"detail": f"Dispositivo transferido exitosamente a {nuevo_propietario_email}."},
            status=status.HTTP_200_OK
        )


class DeviceReportStateView(APIView):
    permission_classes = [IsAuthenticated, IsDeviceOwner]

    def patch(self, request, pk):
        device = get_object_or_404(Dispositivo, id_dispositivo=pk)
        self.check_object_permissions(request, device)

        nuevo_estado = request.data.get("estado")
        if not nuevo_estado:
            return Response(
                {"detail": "Debes proporcionar el campo 'estado'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            device = DeviceService.report_device_state(device, nuevo_estado)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(DispositivoSerializer(device).data, status=status.HTTP_200_OK)


class DeviceReportStolenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device_id = request.data.get("device_id")
        imei = request.data.get("imei")
        motivo = request.data.get("motivo", "Reportado como robado/extraviado")

        if not device_id and not imei:
            return Response(
                {"detail": "Debes proporcionar 'device_id' o 'imei' para reportar el robo."},
                status=status.HTTP_400_BAD_REQUEST
            )

        device = None
        if device_id:
            device = Dispositivo.objects.filter(id_dispositivo=device_id, id_usuario_propietario=request.user).first()
        elif imei:
            device = Dispositivo.objects.filter(hash_imei=imei, id_usuario_propietario=request.user).first()
            if not device:
                imei_hash = hashlib.sha256(imei.encode("utf-8")).hexdigest()
                device = Dispositivo.objects.filter(hash_imei=imei_hash, id_usuario_propietario=request.user).first()

        if not device:
            return Response(
                {"detail": "Dispositivo no encontrado o no pertenece al usuario autenticado."},
                status=status.HTTP_404_NOT_FOUND
            )

        if device.estado != "LIBRE":
            return Response(
                {"detail": f"El dispositivo ya se encuentra en estado {device.estado}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        estado_previo = device.estado

        # Cambiar estado usando el servicio de dispositivo
        try:
            device = DeviceService.report_device_state(device, "ROBADO")
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Registrar la trazabilidad del cambio
        trazabilidad = HistorialTrazabilidad.objects.create(
            id_celular=device,
            estado_anterior=estado_previo,
            estado_nuevo="ROBADO",
            motivo=motivo
        )

        # Registrar en logs de auditoría de SaaS
        UsageLog.objects.create(
            usuario=request.user,
            tipo_accion="reporte_robo_creado",
            dispositivo_id=str(device.id_dispositivo)
        )

        payload = {
            "mensaje": "Dispositivo reportado como robado exitosamente.",
            "dispositivo": DispositivoSerializer(device).data,
            "trazabilidad": HistorialTrazabilidadSerializer(trazabilidad).data
        }

        return Response(payload, status=status.HTTP_200_OK)