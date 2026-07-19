import logging

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction

from accounts.models import TelegramUser
from communication.models import Chat, ChatMembership
from bot_management.models import Bot, PluginDefinition, PluginState
from bot_templates.models import TemplatePack

log = logging.getLogger(__name__)


def compare_plugin_contracts(expected, actual):
    errors = []
    expected_names = set(expected)
    actual_names = set(actual)
    for name in sorted(expected_names - actual_names):
        errors.append({"type": "missing_plugin", "plugin": name, "expected": expected[name]})
    for name in sorted(actual_names - expected_names):
        errors.append({"type": "unexpected_plugin", "plugin": name, "actual": actual[name]})

    for name in sorted(expected_names & actual_names):
        expected_contract = expected[name]
        actual_contract = actual[name]
        expected_fields = expected_contract.get("fields", {})
        actual_fields = actual_contract.get("fields", {})
        for field in sorted(set(expected_fields) - set(actual_fields)):
            errors.append({"type": "missing_field", "plugin": name, "field": field, "expected": expected_fields[field]})
        for field in sorted(set(actual_fields) - set(expected_fields)):
            errors.append({"type": "unexpected_field", "plugin": name, "field": field, "actual": actual_fields[field]})
        for field in sorted(set(expected_fields) & set(actual_fields)):
            if expected_fields[field] != actual_fields[field]:
                errors.append({
                    "type": "field_contract_mismatch",
                    "plugin": name,
                    "field": field,
                    "expected": expected_fields[field],
                    "actual": actual_fields[field],
                })
        if expected_contract.get("additional_fields", True) != actual_contract.get("additional_fields", True):
            errors.append({
                "type": "additional_fields_mismatch",
                "plugin": name,
                "expected": expected_contract.get("additional_fields", True),
                "actual": actual_contract.get("additional_fields", True),
            })
    return errors


@api_view(["POST"])
def validate_runner_contracts(request):
    actual = request.data.get("plugins")
    if not isinstance(actual, dict):
        return Response({"error": "plugins must be an object"}, status=400)

    expected = {
        definition.code: definition.runtime_schema
        for definition in PluginDefinition.objects.filter(is_active=True)
    }
    errors = compare_plugin_contracts(expected, actual)
    return Response({
        "status": "compatible" if not errors else "incompatible",
        "errors": errors,
    })


@api_view(["POST"])
def get_context(request):
    user_data = request.data.get("user")
    chat_data = request.data.get("chat")

    bot : Bot | None = getattr(request, "bot", None)
    log.info("Context request for bot %s", bot.name)

    if not user_data or not chat_data:
        return Response({"error": "user and chat required"}, status=400)

    with transaction.atomic():

        user, _ = upsert_user(user_data)

        chat, _ = upsert_chat(chat_data)
        admin_level = user.admin_level


        ChatMembership.objects.update_or_create(
            user=user,
            chat=chat,
            defaults={
                "joined_at": timezone.now()
            }
        )

        




    

    return Response({
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "admin" : admin_level

        },
        "chat": {
            "id": chat.id,
            "telegram_id": chat.chat_id,
            "type": chat.type,
            "title": chat.title,
        },
    })


@api_view(["POST"])
def save_plugin_state(request):
    plugin_name = request.data.get("plugin")
    state = request.data.get("state")
    bot : Bot | None = getattr(request, "bot", None)

    if not plugin_name:
        return Response({"error": "plugin required"}, status=400)

    if state is None:
        return Response({"error": "state required"}, status=400)

    if not isinstance(state, dict):
        return Response({"error": "state must be an object"}, status=400)

    if not isinstance(plugin_name, str) or len(plugin_name) > 100:
        return Response({"error": "invalid plugin"}, status=400)

    if any(not isinstance(key, str) or not key or len(key) > 255 for key in state):
        return Response({"error": "invalid state key"}, status=400)

    with transaction.atomic():
        for key, value in state.items():
            PluginState.objects.update_or_create(
                bot=bot,
                plugin_code=plugin_name,
                key=key,
                defaults={"value": value},
            )

    states = PluginState.objects.filter(bot=bot, plugin_code=plugin_name)
    state_dict = {state.key: state.value for state in states}
    log.info("Saved state for bot %s, plugin %s", bot.name, plugin_name)
    return Response({"status": "success", "state": state_dict})

@api_view(["GET"])
def load_plugin_state(request):
    plugin_name = request.query_params.get("plugin")
    bot : Bot | None = getattr(request, "bot", None)

    if not plugin_name:
        return Response({"error": "plugin required"}, status=400)

    states = PluginState.objects.filter(bot=bot, plugin_code=plugin_name)
    state_dict = {state.key: state.value for state in states}
    log.info("Loaded state for bot %s, plugin %s", bot.name, plugin_name)
    return Response({"status": "success", "state": state_dict})

def upsert_user(user_data):
    telegram_id = user_data["id"]
    username = user_data.get("username")

    user = TelegramUser.objects.filter(
        telegram_id=telegram_id
    ).first()

    if user:
        changed_fields = []

        if user.username != username:
            user.username = username
            changed_fields.append("username")

       

        if changed_fields:
            user.save(update_fields=changed_fields)

        return user, False

    user = None
    if username:
        user = TelegramUser.objects.filter(
            username=username,
            is_placeholder=True
        ).first()

    if user:
        user.telegram_id = telegram_id
        user.is_placeholder = False

        
        user.save(update_fields=[
            "telegram_id",
            "is_placeholder",
        ])

        return user, False

    return TelegramUser.objects.create(
        telegram_id=telegram_id,
        username=username,
    ), True


def upsert_chat(chat_data):
    telegram_id = chat_data["id"]
    chat_type = chat_data.get("type")
    title = chat_data.get("title")

    chat = Chat.objects.filter(
        chat_id=telegram_id
    ).first()

    if chat:
        changed_fields = []

        if chat.type != chat_type:
            chat.type = chat_type
            changed_fields.append("type")

        if chat.title != title:
            chat.title = title
            changed_fields.append("title")

        if changed_fields:
            chat.save(update_fields=changed_fields)

        return chat, False
    
    return Chat.objects.create(
        chat_id=telegram_id,
        type=chat_type,
        title=title,
    ), True


@api_view(["GET"])
def get_active_bots(request):
    bot_runner = request.bot_runner
    active_bots = Bot.objects.filter(is_active=True, runner=bot_runner)

    bot_list = [
        {
            "name": bot.name,
            "platform": bot.platform,
            "plugins": [
                {"name": item.plugin.code, **item.config}
                for item in bot.plugins.select_related("plugin").filter(is_enabled=True)
            ],
            "services": bot.services,
            "actions": bot.actions,
            "token": bot.token,
            "api_key": bot.api_key,
            "version": bot.version,

        }
        for bot in active_bots
    ]

    return Response({"active_bots": bot_list})


@api_view(["GET"])
def get_template_pack(request):
    plugin = request.query_params.get("plugin")
    template = request.query_params.get("template")
    bot : Bot | None = getattr(request, "bot", None)

    if (plugin == None or template == None):
        return Response({"error" : "plugin name and template name are required"},status=400)
    
    template_pack = TemplatePack.objects.filter(plugin_name = plugin,code = template,bot = bot).first()

    if (template_pack):
        


        return Response({
            "template_pack": {
                "plugin_name": template_pack.plugin_name,
                "key": template_pack.code,
                "data": template_pack.data,
                "variables_schema": template_pack.variables_schema,
                "version": template_pack.version,
                "type": template_pack.data_type,
                }
            }
        )
    else:
        return Response({"error" : "template_pack_not_found"} , status=404)
