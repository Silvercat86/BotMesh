from django.urls import path
from .views import get_context, load_plugin_state, save_data, save_plugin_state, get_active_bots



urlpatterns = [
    path("context/", get_context, name="get_context"),
    path("save_data/", save_data, name="save_data"),
    path("save_plugin_state/", save_plugin_state, name="save_plugin_state"),
    path("load_plugin_state/", load_plugin_state, name="load_plugin_state"),
    path("active_bots/", get_active_bots, name="get_active_bots"),
]


