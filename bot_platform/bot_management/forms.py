from django import forms

from communication.models import Chat


class PluginConfigForm(forms.Form):
    def __init__(self, *args, plugin_definition, current_config, bot, **kwargs):
        super().__init__(*args, **kwargs)

        self.plugin_definition = plugin_definition
        self.current_config = current_config or {}
        self.bot = bot

        schema = plugin_definition.config_schema or {}

        merged_config = {
            **(plugin_definition.default_config or {}),
            **self.current_config,
        }

        for key, field_schema in schema.items():
            field_type = field_schema.get("type")
            label = field_schema.get("label", key)
            value = merged_config.get(key)

            if field_type == "int":
                self.fields[key] = forms.IntegerField(
                    label=label,
                    min_value=field_schema.get("min"),
                    max_value=field_schema.get("max"),
                    initial=value,
                    required=False,
                )

            elif field_type == "chat":
                choices = [("", "Не выбрано")]

                chats = Chat.objects.filter(
                    platform=bot.platform,
                ).order_by("title", "chat_id")

                for chat in chats:
                    title = chat.title or str(chat.chat_id)
                    choices.append((str(chat.chat_id), title))

                self.fields[key] = forms.ChoiceField(
                    label=label,
                    choices=choices,
                    initial="" if value is None else str(value),
                    required=False,
                )

            elif field_type == "bool":
                self.fields[key] = forms.BooleanField(
                    label=label,
                    initial=bool(value),
                    required=False,
                )

            else:
                self.fields[key] = forms.CharField(
                    label=label,
                    initial="" if value is None else str(value),
                    required=False,
                )

    def apply_to_config(self):
        result = dict(self.current_config)

        schema = self.plugin_definition.config_schema or {}

        for key, field_schema in schema.items():
            field_type = field_schema.get("type")
            value = self.cleaned_data.get(key)

            if field_type == "int":
                result[key] = value

            elif field_type == "chat":
                result[key] = int(value) if value else ""

            elif field_type == "bool":
                result[key] = bool(value)

            else:
                result[key] = value

        return result