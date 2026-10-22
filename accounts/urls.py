from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.user_login, name="login"),
    path("signup/", views.signup, name="signup"),
    path("logout/", views.user_logout, name="logout"),
    path("settings/", views.account_settings, name="settings"),
    path("settings/delete/", views.delete_account, name="delete_account"),
]
