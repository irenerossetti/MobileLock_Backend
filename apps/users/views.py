from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction

from .serializers import RegisterSerializer, UserSerializer, UpdateUserSerializer
from .services import UserPlanService, UserService


class UserProfileView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Obtener perfil del usuario autenticado
        """
        user = UserPlanService.sync_plan_flags(request.user)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def put(self, request):
        """
        Actualizar datos del perfil
        """
        user = request.user
        serializer = UpdateUserSerializer(user, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        try:

            refresh_token = request.data["refresh"]

            token = RefreshToken(refresh_token)

            token.blacklist()

            return Response({"message": "Logout exitoso"})

        except Exception:

            return Response({"error": "Token inválido"}, status=400)
    
class RegisterView(APIView):

    def post(self, request):

        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            with transaction.atomic():
                user = serializer.save()
                plan_id = request.data.get("plan_id")

                if plan_id and not UserPlanService.assign_plan(user, plan_id):
                    return Response(
                        {"detail": "Plan seleccionado inválido."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            return Response(
                {
                    "message": "Usuario creado correctamente",
                    "plan_suscripcion": user.plan_suscripcion,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpgradePlanView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get("plan_id")

        if not plan_id:
            return Response(
                {"detail": "plan_id es requerido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        actualizado = UserPlanService.assign_plan(request.user, plan_id)

        if not actualizado:
            return Response(
                {"detail": "No se pudo asignar el plan seleccionado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "message": "Plan actualizado correctamente.",
                "plan_suscripcion": request.user.plan_suscripcion,
            },
            status=status.HTTP_200_OK,
        )


class UserMeView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = UserPlanService.sync_plan_flags(
            UserService.get_user_profile(request.user.id)
        )

        serializer = UserSerializer(user)

        return Response(serializer.data)


    def put(self, request):

        user = UserService.get_user_profile(request.user.id)

        updated_user = UserService.update_user_profile(user, request.data)

        serializer = UserSerializer(updated_user)

        return Response(serializer.data)



class SearchUserView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        query = request.query_params.get("q")

        if not query:
            return Response({"error": "Debe enviar parámetro q"}, status=400)

        users = Usuario.objects.filter(
            nombres__icontains=query
        ) | Usuario.objects.filter(
            correo_electronico__icontains=query
        )

        serializer = UserSerializer(users, many=True)

        return Response(serializer.data)


class VerifyPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        password = request.data.get("password")
        if not password:
            return Response({"detail": "La contraseña es requerida."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if user.check_password(password):
            return Response({"message": "Contraseña válida."}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Contraseña incorrecta."}, status=status.HTTP_403_FORBIDDEN)

