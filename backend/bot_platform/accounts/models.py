from django.db import models

class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True,null = True,blank=True)

    username = models.CharField(max_length=255, null=True, blank=True)

    is_placeholder = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_admin(self) -> bool:
        return hasattr(self, 'administrator')
    
    @property
    def admin_level(self):
        return self.administrator.level if self.is_admin else None

    def __str__(self):
        return f"{self.username or ''}"



class Administrator(models.Model):
    class Level(models.TextChoices):
        SUPER = "super"
        STANDARD = "standard"

    user = models.OneToOneField(TelegramUser, on_delete=models.CASCADE, related_name="administrator")
    level = models.CharField(max_length=20, choices=Level.choices)