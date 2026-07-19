from django.db import migrations, models


def create_runtime_schemas(apps, schema_editor):
    PluginDefinition = apps.get_model("bot_management", "PluginDefinition")
    type_map = {
        "int": {"type": "integer"},
        "bool": {"type": "boolean"},
        "chat": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
        "string": {"type": "string"},
    }
    for definition in PluginDefinition.objects.all().iterator():
        fields = {}
        for name, field in (definition.config_schema or {}).items():
            contract = dict(type_map.get(field.get("type"), {"type": "string"}))
            for source, target in (("min", "minimum"), ("max", "maximum")):
                if source in field:
                    contract[target] = field[source]
            contract["required"] = bool(field.get("required", False))
            fields[name] = contract
        definition.runtime_schema = {
            "fields": fields,
            "additional_fields": False,
        }
        definition.save(update_fields=["runtime_schema"])


class Migration(migrations.Migration):
    dependencies = [
        ("bot_management", "0006_generate_bot_api_key"),
    ]
    operations = [
        migrations.AddField(
            model_name="plugindefinition",
            name="runtime_schema",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.RunPython(create_runtime_schemas, reverse_code=migrations.RunPython.noop),
    ]
