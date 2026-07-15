from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction

from accounts.models import TelegramUser
from communication.models import Chat, ChatMembership
from bot_management.models import Bot, PluginState,BotRunner
from bot_templates.models import TemplatePack

@api_view(["POST"])
def save_data(request):
    bot : Bot | None = getattr(request, "bot", None)
    data = request.data.get("data", {})
    print(f"Data received from bot {bot.name if bot else 'unknown'}: {data}")
    return Response({"status": "success"})


@api_view(["POST"])
def get_context(request):
    user_data = request.data.get("user")
    chat_data = request.data.get("chat")

    bot : Bot | None = getattr(request, "bot", None)
    if bot:
        print(f"Context request for bot {bot.name} (api_key={bot.api_key})")

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

    for key, value in state.items():
        PluginState.objects.update_or_create(
            bot=bot,
            plugin_code=plugin_name,
            key=key,
            defaults={"value": value},
        )

    states = PluginState.objects.filter(bot=bot, plugin_code=plugin_name)
    state_dict = {state.key: state.value for state in states}
    print(f"Saved state for bot {bot.name if bot else 'unknown'} for plugin {plugin_name}: {state_dict}")
    return Response({"status": "success", "state": state_dict})

@api_view(["GET"])
def load_plugin_state(request):
    plugin_name = request.query_params.get("plugin")
    bot : Bot | None = getattr(request, "bot", None)

    if not plugin_name:
        return Response({"error": "plugin required"}, status=400)

    print(f"Loading state for bot {bot.name if bot else 'unknown'} for plugin {plugin_name}")

    states = PluginState.objects.filter(bot=bot, plugin_code=plugin_name)
    state_dict = {state.key: state.value for state in states}
    print(f"Loaded state for bot {bot.name if bot else 'unknown'} for plugin {plugin_name}: {state_dict}")
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
    api_key = request.headers.get("X-API-KEY")

    try:
        BotRunner.objects.get(
            token=api_key,
            is_active=True,
        )
    except BotRunner.DoesNotExist:
        return Response({"error": "forbidden"}, status=403)


    active_bots = Bot.objects.filter(is_active=True)

    bot_list = [
        {
            "name": bot.name,
            "platform": bot.platform,
            "plugins": bot.plugins,
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