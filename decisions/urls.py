from django.urls import path
from . import views

app_name = 'decisions'

urlpatterns = [
    path('<int:dataset_id>/', views.dataset_decisions, name='list'),
    path("filtered/", views.filtered_decisions, name="filtered"),
]
