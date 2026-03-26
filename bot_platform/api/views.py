from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction

from accounts.models import TelegramUser, Membership
from communication.models import Chat


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
                "company" : request.company,
            }
        )

        
        membership, _ = Membership.objects.get_or_create(
            user=user,
            company=request.company,
            defaults={
                "role": Membership.Role.EMPLOYEE
            }
        )

        role = membership.role if membership else None

    return Response({
        "user_id": user.id,
        "chat_id": chat.id,
        "role": role,
    })


def upsert_user(user_data):
    user = TelegramUser.objects.filter(
        telegram_id=user_data["id"]
    ).first()

    if not user:
        return TelegramUser.objects.create(
            telegram_id=user_data["id"],
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
        ), True

    changed_fields = []

    if user.username != user_data.get("username"):
        user.username = user_data.get("username")
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