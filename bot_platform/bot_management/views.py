from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from .forms import BotForm, PluginConfigForm
from .models import Bot, BotAccess, BotPlugin, PluginDefinition


class DashboardLoginView(LoginView):
    template_name = "dashboard/login.html"
    redirect_authenticated_user = True
    def get_success_url(self): return reverse_lazy("dashboard_home")


class DashboardLogoutView(LogoutView):
    next_page = reverse_lazy("dashboard_login")


def accessible_bots(user):
    if user.is_superuser:
        return Bot.objects.all()
    return Bot.objects.filter(user_accesses__user=user).distinct()


def bot_for_user(user, bot_id, manage=False):
    bot = get_object_or_404(accessible_bots(user), pk=bot_id)
    if manage and not user.is_superuser:
        access = get_object_or_404(BotAccess, user=user, bot=bot)
        if not access.can_manage:
            raise PermissionDenied
    return bot


@login_required(login_url="dashboard_login")
def home(request):
    bots = accessible_bots(request.user)
    return render(request, "dashboard/home.html", {"bots": bots, "active_count": bots.filter(is_active=True).count()})


@login_required(login_url="dashboard_login")
def bot_list(request):
    return render(request, "dashboard/bot_list.html", {"bots": accessible_bots(request.user).order_by("name")})


@login_required(login_url="dashboard_login")
def bot_create(request):
    if not request.user.is_superuser: raise PermissionDenied
    form = BotForm(request.POST or None)
    if form.is_valid():
        bot = form.save()
        return redirect("dashboard_bot_plugins", bot_id=bot.pk)
    return render(request, "dashboard/bot_form.html", {"form": form, "title": "Новый бот"})


@login_required(login_url="dashboard_login")
def bot_edit(request, bot_id):
    if not request.user.is_superuser: raise PermissionDenied
    bot = get_object_or_404(Bot, pk=bot_id)
    form = BotForm(request.POST or None, instance=bot)
    if form.is_valid():
        form.save()
        return redirect("dashboard_bot_plugins", bot_id=bot.pk)
    return render(request, "dashboard/bot_form.html", {"form": form, "title": f"Настройки {bot.name}"})


@login_required(login_url="dashboard_login")
def bot_plugins(request, bot_id):
    bot = bot_for_user(request.user, bot_id)
    installed_ids = bot.plugins.values_list("plugin_id", flat=True)
    available = bot.available_plugins.filter(is_active=True).exclude(pk__in=installed_ids)
    access = None if request.user.is_superuser else BotAccess.objects.get(user=request.user, bot=bot)
    return render(request, "dashboard/bot_plugins.html", {"bot": bot, "plugins": bot.plugins.select_related("plugin"), "available_plugins": available, "can_manage": request.user.is_superuser or access.can_manage})


@login_required(login_url="dashboard_login")
@require_POST
def toggle_bot(request, bot_id):
    bot = bot_for_user(request.user, bot_id, manage=True)
    bot.is_active = not bot.is_active
    bot.save(update_fields=["is_active"])
    return redirect("dashboard_bot_plugins", bot_id=bot.pk)


@login_required(login_url="dashboard_login")
@require_POST
def add_plugin_to_bot(request, bot_id, plugin_code):
    bot = bot_for_user(request.user, bot_id, manage=True)
    definition = get_object_or_404(bot.available_plugins, code=plugin_code, is_active=True)
    BotPlugin.objects.create(bot=bot, plugin=definition, config=dict(definition.default_config or {}))
    return redirect("dashboard_bot_plugins", bot_id=bot.pk)


@login_required(login_url="dashboard_login")
def edit_bot_plugin(request, bot_id, plugin_id):
    bot = bot_for_user(request.user, bot_id, manage=True)
    bot_plugin = get_object_or_404(BotPlugin, pk=plugin_id, bot=bot)
    form = PluginConfigForm(request.POST or None, bot_plugin=bot_plugin)
    if request.method == "POST" and form.is_valid():
        form.apply()
        return redirect("dashboard_bot_plugins", bot_id=bot.pk)
    return render(request, "dashboard/edit_bot_plugin.html", {"bot": bot, "bot_plugin": bot_plugin, "form": form})


@login_required(login_url="dashboard_login")
@require_POST
def toggle_bot_plugin(request, bot_id, plugin_id):
    bot = bot_for_user(request.user, bot_id, manage=True)
    item = get_object_or_404(BotPlugin, pk=plugin_id, bot=bot)
    item.is_enabled = not item.is_enabled
    item.save(update_fields=["is_enabled", "updated_at"])
    return redirect("dashboard_bot_plugins", bot_id=bot.pk)


@login_required(login_url="dashboard_login")
@require_POST
def delete_bot_plugin(request, bot_id, plugin_id):
    bot = bot_for_user(request.user, bot_id, manage=True)
    get_object_or_404(BotPlugin, pk=plugin_id, bot=bot).delete()
    return redirect("dashboard_bot_plugins", bot_id=bot.pk)
