from django.urls import path
from .views import (
    RegisterView,
    UserMeView,
    SearchUserView,
    LogoutView
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # AUTH
    path('auth/register/', RegisterView.as_view()),
    path('auth/login/', TokenObtainPairView.as_view()),
    path('auth/token/refresh/', TokenRefreshView.as_view()),
    path('auth/logout/', LogoutView.as_view()),

    # USERS - Quita el 'users/' adicional
    path('me/', UserMeView.as_view()),  # ← Cambiado de 'users/me/' a 'me/'
    path('search/', SearchUserView.as_view()),  # ← Cambiado de 'users/search/' a 'search/'
]