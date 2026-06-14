import hashlib
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from apps.devices.models import Dispositivo, HistorialEscaneo
from apps.devices.serializers import DispositivoSerializer, HistorialEscaneoSerializer
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


class HistorialEscaneoListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        historial = HistorialEscaneo.objects.filter(usuario=request.user)
        serializer = HistorialEscaneoSerializer(historial, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)