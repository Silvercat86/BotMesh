from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction

from accounts.models import TelegramUser
from communication.models import Chat

def resolve_permissions(role):
    return {
        "can_manage_company": role in ["hr"],
        "can_manage_employees": role in ["hr", "manager"],
        "can_manage_offers": role in ["hr", "manager"],
    }


@api_view(["POST"])
def get_context(request):
    user_data = request.data.get("user")
    chat_data = request.data.get("chat")

    if not user_data or not chat_data:
        return Response({"error": "user and chat required"}, status=400)

    with transaction.atomic():

        user, _ = upsert_user(user_data)

        chat, _ = Chat.objects.update_or_create(
            telegram_id=chat_data["id"],
            defaults={
                "type": chat_data.get("type"),
                "title": chat_data.get("title"),
            }
        )

        role = None
        admin = user.admin
        admin_level = admin.level if admin else None




    

    return Response({
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "admin" : admin_level

        },
        "chat": {
            "id": chat.id,
            "telegram_id": chat.telegram_id,
        },
        
        "permissions": resolve_permissions(role)
    })


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