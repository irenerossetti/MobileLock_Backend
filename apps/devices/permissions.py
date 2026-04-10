from rest_framework.permissions import BasePermission


class IsDeviceOwner(BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.id_usuario_propietario == request.user