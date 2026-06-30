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
        "name": plugin_definition.code,
        **(plugin_definition.default_config or {}),
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


@staff_required
def raw_bot_config(request, bot_id):
    bot = get_object_or_404(Bot, id=bot_id)

    if request.method == "POST":
        plugins_raw = request.POST.get("plugins", "[]")
        services_raw = request.POST.get("services", "[]")
        actions_raw = request.POST.get("actions", "[]")

        try:
            plugins = json.loads(plugins_raw)
            services = json.loads(services_raw)
            actions = json.loads(actions_raw)
        except json.JSONDecodeError as error:
            return render(request, "dashboard/raw_bot_config.html", {
                "bot": bot,
                "plugins_json": plugins_raw,
                "services_json": services_raw,
                "actions_json": actions_raw,
                "error": f"JSON ошибка: {error}",
            })

        if not isinstance(plugins, list):
            return render(request, "dashboard/raw_bot_config.html", {
                "bot": bot,
                "plugins_json": plugins_raw,
                "services_json": services_raw,
                "actions_json": actions_raw,
                "error": "plugins должен быть списком JSON.",
            })

        if not isinstance(services, list):
            return render(request, "dashboard/raw_bot_config.html", {
                "bot": bot,
                "plugins_json": plugins_raw,
                "services_json": services_raw,
                "actions_json": actions_raw,
                "error": "services должен быть списком JSON.",
            })

        if not isinstance(actions, list):
            return render(request, "dashboard/raw_bot_config.html", {
                "bot": bot,
                "plugins_json": plugins_raw,
                "services_json": services_raw,
                "actions_json": actions_raw,
                "error": "actions должен быть списком JSON.",
            })

        bot.plugins = plugins
        bot.services = services
        bot.actions = actions
        bot.save()

        return redirect("dashboard_bot_plugins", bot_id=bot.id)

    return render(request, "dashboard/raw_bot_config.html", {
        "bot": bot,
        "plugins_json": json.dumps(bot.plugins or [], ensure_ascii=False, indent=4),
        "services_json": json.dumps(bot.services or [], ensure_ascii=False, indent=4),
        "actions_json": json.dumps(bot.actions or [], ensure_ascii=False, indent=4),
        "error": None,
    })


def build_runner_plugins(bot):
    result = []

    for plugin in bot.plugins or []:
        if plugin.get("enabled") is False:
            continue

        if not plugin.get("name"):
            continue

        result.append(plugin)

    return result


def runner_bot_version(request, api_key):
    bot = get_object_or_404(Bot, api_key=api_key)

    return JsonResponse({
        "is_active": bot.is_active,
        "version": bot.version,
    })


def runner_bot_config(request, api_key):
    bot = get_object_or_404(
        Bot,
        api_key=api_key,
        is_active=True,
    )

    return JsonResponse({
        "bot": {
            "name": bot.name,
            "platform": bot.platform,
            "version": bot.version,
            "is_active": bot.is_active,
        },
        "plugins": build_runner_plugins(bot),
        "services": bot.services or [],
        "actions": bot.actions or [],
    })