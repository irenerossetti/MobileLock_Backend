from django.urls import path
from .views import (
    RegisterView,
    UserMeView,
    SearchUserView,
    LogoutView,
    UserProfileView,
    UpgradePlanView,
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [

    # AUTH
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),

    # PROFILE (usuario autenticado)
    path("profile/get/", UserProfileView.as_view(), name="user-profile-get"),
    path("profile/update/", UserProfileView.as_view(), name="user-profile-update"),
    path("plan/upgrade/", UpgradePlanView.as_view(), name="user-plan-upgrade"),

    # USERS
    path("users/me/", UserMeView.as_view(), name="user-me"),
    path("users/search/", SearchUserView.as_view(), name="user-search"),
]