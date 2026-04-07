from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import Usuario
from .serializers import RegisterSerializer, UserSerializer, UpdateUserSerializer
from .services import UserService


class UserProfileView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Obtener perfil del usuario autenticado
        """
        user = request.user
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
            serializer.save()
            return Response({"message": "Usuario creado correctamente"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserMeView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = UserService.get_user_profile(request.user.id)

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

