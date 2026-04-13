from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from apps.devices.models import Dispositivo
from apps.devices.serializers import DispositivoSerializer
from apps.devices.permissions import IsDeviceOwner
from apps.devices.services import DeviceService


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