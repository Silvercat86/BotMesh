from aiogram.types import User,Chat


def build_user_payload(user:User):
    return {
        "tg_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }

def build_chat_payload(chat:Chat):
    return{
        "tg_id": chat.id,
        "type": chat.type,
        "title": getattr(chat, "title", None),
    }