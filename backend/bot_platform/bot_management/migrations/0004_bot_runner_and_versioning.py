import django.db.models.deletion
from django.db import migrations, models


def assign_bots_to_single_runner(apps, schema_editor):
    Bot = apps.get_model("bot_management", "Bot")
    BotRunner = apps.get_model("bot_management", "BotRunner")
    runners = list(BotRunner.objects.values_list("pk", flat=True)[:2])
    if len(runners) == 1:
        Bot.objects.filter(runner__isnull=True).update(runner_id=runners[0])


class Migration(migrations.Migration):
    dependencies = [
        ("bot_management", "0003_rename_token_botrunner_api_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="bot",
            name="runner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="bots",
                to="bot_management.botrunner",
            ),
        ),
        migrations.RunPython(
            assign_bots_to_single_runner,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="bot",
            name="version",
            field=models.PositiveBigIntegerField(default=1, editable=False),
        ),
        migrations.AlterUniqueTogether(
            name="pluginstate",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="pluginstate",
            constraint=models.UniqueConstraint(
                fields=("bot", "plugin_code", "key"),
                name="unique_bot_plugin_state_key",
            ),
        ),
    ]
