from apps.users.models import Usuario


class UserService:

    @staticmethod
    def get_user_profile(user_id):
        return Usuario.objects.get(id=user_id)

    @staticmethod
    def update_user_profile(user, data):

        user.nombres = data.get("nombres", user.nombres)
        user.apellido_paterno = data.get("apellido_paterno", user.apellido_paterno)
        user.apellido_materno = data.get("apellido_materno", user.apellido_materno)

        user.save()

        return user
    @staticmethod
    def search_users(query):

        return Usuario.objects.filter(
            nombres__icontains=query
        ) | Usuario.objects.filter(
            correo_electronico__icontains=query
        )