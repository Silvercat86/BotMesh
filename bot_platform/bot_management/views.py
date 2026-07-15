import json

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from .forms import PluginConfigForm
from .models import Bot, PluginDefinition


def staff_required(view_func):
    return user_passes_test(
        lambda user: user.is_authenticated and user.is_staff,
        login_url="dashboard_login",
    )(view_func)


class DashboardLoginView(LoginView):
    template_name = "dashboard/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("dashboard_bot_list")


class DashboardLogoutView(LogoutView):
    next_page = reverse_lazy("dashboard_login")


@staff_required
def bot_list(request):
    bots = Bot.objects.all().order_by("name")

    return render(request, "dashboard/bot_list.html", {
        "bots": bots,
    })


@staff_required
def bot_plugins(request, bot_id):
    bot = get_object_or_404(Bot, id=bot_id)

    available_plugins = PluginDefinition.objects.filter(
        is_active=True,
    ).order_by("title", "code")

    return render(request, "dashboard/bot_plugins.html", {
        "bot": bot,
        "plugins": bot.plugins or [],
        "available_plugins": available_plugins,
    })


@staff_required
@require_POST
def add_plugin_to_bot(request, bot_id, plugin_code):
    bot = get_object_or_404(Bot, id=bot_id)

    plugin_definition = get_object_or_404(
        PluginDefinition,
        code=plugin_code,
        is_active=True,
    )

    plugin_item = {
        **(plugin_definition.default_config or {}),
        "name": plugin_definition.code,
    }

    plugins = list(bot.plugins or [])
    plugins.append(plugin_item)

    bot.plugins = plugins
    bot.save()

    return redirect("dashboard_bot_plugins", bot_id=bot.id)


@staff_required
def edit_bot_plugin(request, bot_id, plugin_index):
    bot = get_object_or_404(Bot, id=bot_id)

    plugins = list(bot.plugins or [])

    try:
        plugin_item = plugins[plugin_index]
    except IndexError:
        raise Http404("Plugin not found")

    plugin_name = plugin_item.get("name")

    if not plugin_name:
        raise Http404("Plugin has no name")

    plugin_definition = get_object_or_404(
        PluginDefinition,
        code=plugin_name,
        is_active=True,
    )

    if request.method == "POST":
        form = PluginConfigForm(
            request.POST,
            plugin_definition=plugin_definition,
            current_config=plugin_item,
            bot=bot,
        )

        if form.is_valid():
            updated_plugin_item = form.apply_to_config()
            updated_plugin_item["name"] = plugin_name

            plugins[plugin_index] = updated_plugin_item

            bot.plugins = plugins
            bot.save()

            return redirect("dashboard_bot_plugins", bot_id=bot.id)

    else:
        form = PluginConfigForm(
            plugin_definition=plugin_definition,
            current_config=plugin_item,
            bot=bot,
        )

    return render(request, "dashboard/edit_bot_plugin.html", {
        "bot": bot,
        "plugin_index": plugin_index,
        "plugin_item": plugin_item,
        "plugin_definition": plugin_definition,
        "form": form,
    })


@staff_required
@require_POST
def delete_bot_plugin(request, bot_id, plugin_index):
    bot = get_object_or_404(Bot, id=bot_id)

    plugins = list(bot.plugins or [])

    try:
        plugins.pop(plugin_index)
    except IndexError:
        raise Http404("Plugin not found")

    bot.plugins = plugins
    bot.save()

    return redirect("dashboard_bot_plugins", bot_id=bot.id)