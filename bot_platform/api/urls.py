from django.urls import path
from . import views

urlpatterns = [
    path("context/", views.get_context),
    


]
