from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction

from accounts.models import TelegramUser
from communication.models import Bot, Chat, ChatMembership

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

    if not plugin_name or state is None:
        return Response({"error": "plugin and state required"}, status=400)

    print(f"Saving state for bot {bot.name if bot else 'unknown'} for plugin {plugin_name}: {state}")

    return Response(state)

@api_view(["GET"])
def load_plugin_state(request):
    plugin_name = request.query_params.get("plugin")
    bot : Bot | None = getattr(request, "bot", None)

    if not plugin_name:
        return Response({"error": "plugin required"}, status=400)

    print(f"Loading state for bot {bot.name if bot else 'unknown'} for plugin {plugin_name}")

    example_state = {
        "example_key": "example_value"
    }
    return Response(example_state)

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

    