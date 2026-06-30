from django import forms

from communication.models import Chat, Template


class PluginConfigForm(forms.Form):
    def __init__(self, *args, plugin_definition, current_config, bot, **kwargs):
        super().__init__(*args, **kwargs)

        self.plugin_definition = plugin_definition
        self.current_config = current_config or {}
        self.bot = bot
        self.schema = plugin_definition.config_schema or {}

        merged_config = {
            **(plugin_definition.default_config or {}),
            **self.current_config,
        }

        for key, field_schema in self.schema.items():
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

            elif field_type == "bool":
                self.fields[key] = forms.BooleanField(
                    label=label,
                    initial=bool(value),
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

            elif field_type == "template_group":
                codes = (
                    Template.objects
                    .values_list("code", flat=True)
                    .distinct()
                    .order_by("code")
                )

                self.fields[key] = forms.ChoiceField(
                    label=label,
                    choices=[("", "Не выбрано")] + [(code, code) for code in codes],
                    initial=value or "",
                    required=False,
                )

            elif field_type == "data_source":
                self.fields[key] = forms.CharField(
                    label=label,
                    initial=value or "",
                    required=False,
                )

            elif field_type == "str":
                self.fields[key] = forms.CharField(
                    label=label,
                    initial=value or "",
                    required=False,
                )

            else:
                self.fields[key] = forms.CharField(
                    label=label,
                    initial="" if value is None else str(value),
                    required=False,
                )

    def apply_to_config(self):
        """
        Берём старый dict плагина и меняем только поля из schema.
        Так не теряются поля вроде name/storage_dir, которых нет в config_schema.
        """
        result = dict(self.current_config)

        for key, field_schema in self.schema.items():
            field_type = field_schema.get("type")
            value = self.cleaned_data.get(key)

            if field_type == "int":
                result[key] = value

            elif field_type == "bool":
                result[key] = bool(value)

            elif field_type == "chat":
                result[key] = int(value) if value else None

            elif field_type in ("template_group", "data_source", "str"):
                result[key] = value or None

            else:
                result[key] = value

        return result