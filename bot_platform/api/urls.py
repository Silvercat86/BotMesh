from django.urls import path
from .views import get_context



urlpatterns = [
    path("context/", get_context, name="get_context"),


]


