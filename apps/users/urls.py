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

    # USERS
    path('users/me/', UserMeView.as_view()),
    path('users/search/', SearchUserView.as_view()),
]