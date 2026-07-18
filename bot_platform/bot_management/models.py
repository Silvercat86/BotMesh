import secrets

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F


def generate_bot_api_key():
    return f"bot_{secrets.token_urlsafe(32)}"


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
    runner = models.ForeignKey(
        "BotRunner", on_delete=models.PROTECT, related_name="bots", null=True, blank=True
    )
    available_plugins = models.ManyToManyField(
        PluginDefinition, related_name="available_for_bots", blank=True
    )
    services = models.JSONField(default=list)
    actions = models.JSONField(default=list)
    token = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255, unique=True, default=generate_bot_api_key, editable=False)
    version = models.PositiveBigIntegerField(default=1, editable=False)
    is_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.version = max(self.version, 1) + (1 if self.pk else 0)
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = set(update_fields) | {"version"}
        super().save(*args, **kwargs)

    def bump_version(self):
        type(self).objects.filter(pk=self.pk).update(version=F("version") + 1)
        self.refresh_from_db(fields=["version"])

    def __str__(self):
        status = "active" if self.is_active else "not active"
        return f"{self.name} ({status})"


class BotRunner(models.Model):
    name = models.CharField(max_length=100, unique=True)
    api_key = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        status = "active" if self.is_active else "not active"
        return f"{self.name} ({status})"


class BotAccess(models.Model):
    class Role(models.TextChoices):
        VIEWER = "viewer", "Viewer"
        OPERATOR = "operator", "Operator"
        MANAGER = "manager", "Manager"
        TECHNICAL_ADMIN = "technical_admin", "Technical administrator"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bot_accesses")
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name="user_accesses")
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.VIEWER)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "bot"], name="unique_user_bot_access")]

    @property
    def can_manage(self):
        return self.role != self.Role.VIEWER

    def __str__(self):
        return f"{self.user} → {self.bot} ({self.role})"


class BotPlugin(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name="plugins")
    plugin = models.ForeignKey(PluginDefinition, on_delete=models.PROTECT, related_name="bot_instances")
    is_enabled = models.BooleanField(default=False)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["bot", "plugin"], name="unique_bot_plugin")]

    def clean(self):
        super().clean()
        if self.bot_id and self.plugin_id and not self.bot.available_plugins.filter(pk=self.plugin_id).exists():
            raise ValidationError({"plugin": "Plugin is not available for this bot."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.bot.bump_version()

    def delete(self, *args, **kwargs):
        bot = self.bot
        result = super().delete(*args, **kwargs)
        bot.bump_version()
        return result

    def __str__(self):
        return f"{self.bot.name}: {self.plugin.code}"


class PluginState(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    plugin_code = models.CharField(max_length=100)
    key = models.CharField(max_length=255)
    value = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["bot", "plugin_code", "key"], name="unique_bot_plugin_state_key")]
        indexes = [models.Index(fields=["bot", "plugin_code", "key"])]

    def __str__(self):
        return f"({self.bot.name}) {self.plugin_code} : {self.key} ({self.value})"
