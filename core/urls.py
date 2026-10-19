from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("privacy/", TemplateView.as_view(template_name="core/privacy.html"), name="privacy"),
    path("terms/", TemplateView.as_view(template_name="core/terms.html"), name="terms"),
    path("favicon.ico", views.favicon, name="favicon"),
]
