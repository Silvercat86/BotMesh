from django.db import models

from bot_management.models import Bot

class TemplatePack(models.Model):
    DATA_TYPES = [
        ("dict", "Dict"),
        ("list", "List"),
        ("text", "Text"),
    ]

    bot = models.ForeignKey(
        Bot,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="template_packs",
    )



    plugin_name = models.CharField(max_length=100, db_index=True)
    key = models.CharField(max_length=100, db_index=True)

    data_type = models.CharField(
        max_length=50,
        choices=DATA_TYPES,
        default="dict",
    )

    data = models.JSONField(default=dict)

    variables_schema = models.JSONField(default=dict, blank=True)

    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("bot", "plugin_name", "key")

    def __str__(self):
        bot_name = self.bot.name if self.bot else "GLOBAL"
        return f"{bot_name} / {self.plugin_name} / {self.key}"