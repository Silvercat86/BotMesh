from django.db import models
from accounts.models import TelegramUser

class Platform(models.TextChoices):
    TELEGRAM = "telegram"
    MAX = "max"
class Chat(models.Model):
    class Type(models.TextChoices):
        PRIVATE = "private"
        GROUP = "group"

    chat_id = models.BigIntegerField(unique=True)

    platform = models.CharField(max_length=20, choices=Platform.choices)

    type = models.CharField(max_length=20,choices=Type.choices)
    title = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.type.capitalize()} : {self.title if self.title else "No title"} ({self.platform if self.platform else "No platform"}) "



class Notification(models.Model):
    

    class Type(models.TextChoices):
        BIRTHDAY = "birthday"
        OFFER = "offer"
        REMINDER = "reminder"

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)

    type = models.CharField(max_length=50,choices=Type.choices)
    payload = models.JSONField()

    platform = models.CharField(max_length=20, choices=Platform.choices)

    send_at = models.DateTimeField()

    is_sent = models.BooleanField(default=False)

    error = models.TextField(null=True, blank=True)
    attempts = models.IntegerField(default=0)

    

    class Meta:
        indexes = [
            models.Index(fields=["is_sent", "send_at"]),
        ]


class Template(models.Model):
    code = models.CharField(max_length=100)

    text = models.TextField()




class ChatMembership(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "chat")


