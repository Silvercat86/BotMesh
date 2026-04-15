from django.db import models

class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True,null = True,blank=True)

    username = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, null=True, blank=True)

    is_placeholder = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def admin(self):
        return getattr(self,"administrator",None)

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''} ({self.username or ''})"



class Administrator(models.Model):
    class Level(models.TextChoices):
        SUPER = "super"
        STANDARD = "standard"

    user = models.OneToOneField(TelegramUser, on_delete=models.CASCADE)
    level = models.CharField(max_length=20, choices=Level.choices)