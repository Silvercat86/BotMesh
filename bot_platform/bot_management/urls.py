from django.shortcuts import redirect
from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/login/", views.DashboardLoginView.as_view(), name="dashboard_login"),
    path("dashboard/logout/", views.DashboardLogoutView.as_view(), name="dashboard_logout"),
    path("", lambda request: redirect("dashboard_home")),
    path("dashboard/", views.home, name="dashboard_home"),
    path("dashboard/bots/", views.bot_list, name="dashboard_bot_list"),
    path("dashboard/bots/new/", views.bot_create, name="dashboard_bot_create"),
    path("dashboard/bots/<int:bot_id>/edit/", views.bot_edit, name="dashboard_bot_edit"),
    path("dashboard/bots/<int:bot_id>/toggle/", views.toggle_bot, name="dashboard_toggle_bot"),
    path("dashboard/bots/<int:bot_id>/plugins/", views.bot_plugins, name="dashboard_bot_plugins"),
    path("dashboard/bots/<int:bot_id>/plugins/add/<str:plugin_code>/", views.add_plugin_to_bot, name="dashboard_add_plugin_to_bot"),
    path("dashboard/bots/<int:bot_id>/plugins/<int:plugin_id>/edit/", views.edit_bot_plugin, name="dashboard_edit_bot_plugin"),
    path("dashboard/bots/<int:bot_id>/plugins/<int:plugin_id>/toggle/", views.toggle_bot_plugin, name="dashboard_toggle_bot_plugin"),
    path("dashboard/bots/<int:bot_id>/plugins/<int:plugin_id>/delete/", views.delete_bot_plugin, name="dashboard_delete_bot_plugin"),
]
