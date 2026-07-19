from django.urls import path
from .views import get_context, load_plugin_state, save_plugin_state, get_active_bots,get_template_pack,validate_runner_contracts



urlpatterns = [
    path("context/", get_context, name="get_context"),
    path("save_plugin_state/", save_plugin_state, name="save_plugin_state"),
    path("load_plugin_state/", load_plugin_state, name="load_plugin_state"),
    path("active_bots/", get_active_bots, name="get_active_bots"),
    path("runner/validate_contracts/", validate_runner_contracts, name="validate_runner_contracts"),
    path("get_template_pack/", get_template_pack, name="get_template_pack"),
    
]


