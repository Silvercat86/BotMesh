from django.db import models
from accounts.models import TelegramUser

class Chat(models.Model):
    class Type(models.TextChoices):
        PRIVATE = "private"
        GROUP = "group"

    telegram_id = models.BigIntegerField(unique=True)

    type = models.CharField(max_length=20,choices=Type.choices)
    title = models.CharField(max_length=255, null=True, blank=True)



class Notification(models.Model):
    class Channel(models.TextChoices):
        TELEGRAM = "telegram"
        EMAIL = "email"
        SYSTEM = "system"

    class Type(models.TextChoices):
        BIRTHDAY = "birthday"
        OFFER = "offer"
        REMINDER = "reminder"

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)

    type = models.CharField(max_length=50,choices=Type.choices)
    payload = models.JSONField()

    channel = models.CharField(max_length=20, choices=Channel.choices)

    send_at = models.DateTimeField()

    is_sent = models.BooleanField(default=False)

    error = models.TextField(null=True, blank=True)
    attempts = models.IntegerField(default=0)

    

    class Meta:
        indexes = [
            models.Index(fields=["is_sent", "send_at"]),
        ]


class Template(models.Model):
    code = models.CharField(max_length=100)  # "offer_send", "birthday_1"

    text = models.TextField()





class BotSession(models.Model):
    user = models.OneToOneField(TelegramUser, on_delete=models.CASCADE)

    state = models.CharField(max_length=100)
    data = models.JSONField(default=dict)

    updated_at = models.DateTimeField(auto_now=True)

    


class ChatMembership(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "chat")


class Bot(models.Model):
    token = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255, unique=True)

    is_active = models.BooleanField(default=True)