import bot_management.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bot_management", "0005_bot_access_and_plugins"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bot",
            name="api_key",
            field=models.CharField(
                default=bot_management.models.generate_bot_api_key,
                editable=False,
                max_length=255,
                unique=True,
            ),
        ),
    ]
