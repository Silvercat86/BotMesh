from django.db import models

class Platform(models.TextChoices):
    TELEGRAM = "telegram"
    MAX = "max"


class PluginDefinition(models.Model):
    code = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    default_config = models.JSONField(default=dict)
    config_schema = models.JSONField(default=dict)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    

class Bot(models.Model):
    name = models.CharField(max_length=100, unique=True)
    platform = models.CharField(max_length=20, choices=Platform.choices)

    plugins = models.JSONField(default=list)
    services = models.JSONField(default=list)
    actions = models.JSONField(default=list)

    token = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255, unique=True)

    version = models.IntegerField(default=1)

    is_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.version:
            self.version = 1
        else:
            self.version += 1
            if self.version > 10:
                self.version = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({"active" if self.is_active else "not active"})"
    
class BotRunnerToken(models.Model):
    token = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=False)


class PluginState(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)

    plugin_code = models.CharField(max_length=100)

    key = models.CharField(max_length=255)

    value = models.JSONField(default=dict)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("bot", "plugin_code", "key")
        indexes = [
            models.Index(fields=["bot", "plugin_code", "key"]),
        ]

    def __str__(self):
        return f"({self.bot.name}) {self.plugin_code} : {self.key} ({self.value})"    
    

