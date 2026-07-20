from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_plugins(apps, schema_editor):
    Bot = apps.get_model("bot_management", "Bot")
    BotPlugin = apps.get_model("bot_management", "BotPlugin")
    PluginDefinition = apps.get_model("bot_management", "PluginDefinition")
    for bot in Bot.objects.all().iterator():
        for item in bot.plugins or []:
            if not isinstance(item, dict) or not item.get("name"):
                continue
            code = item["name"]
            definition, _ = PluginDefinition.objects.get_or_create(code=code, defaults={"title": code})
            bot.available_plugins.add(definition)
            config = dict(item)
            config.pop("name", None)
            is_enabled = bool(config.pop("is_enabled", True))
            BotPlugin.objects.update_or_create(bot=bot, plugin=definition, defaults={"config": config, "is_enabled": is_enabled})


class Migration(migrations.Migration):
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("bot_management", "0004_bot_runner_and_versioning")]
    operations = [
        migrations.AddField(model_name="bot", name="available_plugins", field=models.ManyToManyField(blank=True, related_name="available_for_bots", to="bot_management.plugindefinition")),
        migrations.CreateModel(name="BotAccess", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("role", models.CharField(choices=[("viewer", "Viewer"), ("operator", "Operator"), ("manager", "Manager"), ("technical_admin", "Technical administrator")], default="viewer", max_length=30)), ("bot", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_accesses", to="bot_management.bot")), ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bot_accesses", to=settings.AUTH_USER_MODEL))], options={"constraints": [models.UniqueConstraint(fields=("user", "bot"), name="unique_user_bot_access")]}),
        migrations.CreateModel(name="BotPlugin", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("is_enabled", models.BooleanField(default=False)), ("config", models.JSONField(blank=True, default=dict)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)), ("bot", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="plugins", to="bot_management.bot")), ("plugin", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bot_instances", to="bot_management.plugindefinition"))], options={"constraints": [models.UniqueConstraint(fields=("bot", "plugin"), name="unique_bot_plugin")]}),
        migrations.RunPython(migrate_plugins, reverse_code=migrations.RunPython.noop),
        migrations.RemoveField(model_name="bot", name="plugins"),
    ]
