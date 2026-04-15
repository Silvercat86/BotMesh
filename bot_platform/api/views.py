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

        membership = None
        role = None
        company = chat.company
        admin = user.admin
        admin_level = admin.level if admin else None




    

    return Response({
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "admin" : admin_level if admin else None

        },
        "chat": {
            "id": chat.id,
            "telegram_id": chat.telegram_id,
        },
        "company": (
            {
                "id": company.id,
                "name": company.name
            } if company else None
        ),
        "role": role,
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

        if user.first_name != user_data.get("first_name"):
            user.first_name = user_data.get("first_name")
            changed_fields.append("first_name")

        if user.last_name != user_data.get("last_name"):
            user.last_name = user_data.get("last_name")
            changed_fields.append("last_name")

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

        user.first_name = user_data.get("first_name")
        user.last_name = user_data.get("last_name")

        user.save(update_fields=[
            "telegram_id",
            "is_placeholder",
            "first_name",
            "last_name"
        ])

        return user, False

    return TelegramUser.objects.create(
        telegram_id=telegram_id,
        username=username,
        first_name=user_data.get("first_name"),
        last_name=user_data.get("last_name"),
    ), True