from django import forms

from communication.models import Chat
from .models import Bot, BotPlugin


class BotForm(forms.ModelForm):
    bot_name = forms.CharField(
        label="Название бота",
        max_length=100,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )
    token = forms.CharField(
        label="Токен мессенджера",
        required=False,
        widget=forms.Textarea(
            attrs={
                "autocomplete": "off",
                "rows": 1,
                "spellcheck": "false",
                "style": "resize:none;min-height:44px",
            }
        ),
    )

    class Meta:
        model = Bot
        fields = ["platform", "runner", "token", "available_plugins", "is_active"]
        labels = {
            "platform": "Платформа",
            "runner": "Runner",
            "available_plugins": "Доступные модули",
            "is_active": "Бот включён",
        }
        widgets = {
            "available_plugins": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["bot_name"].initial = self.instance.name
            self.fields["token"].help_text = "Оставьте пустым, чтобы сохранить текущий токен."
        else:
            self.fields["token"].help_text = "Введите токен, выданный платформой мессенджера."
        self.order_fields(["bot_name", "platform", "runner", "token", "available_plugins", "is_active"])

    def clean_bot_name(self):
        name = self.cleaned_data["bot_name"].strip()
        duplicate = Bot.objects.filter(name=name).exclude(pk=self.instance.pk).exists()
        if duplicate:
            raise forms.ValidationError("Бот с таким названием уже существует.")
        return name

    def clean_token(self):
        token = self.cleaned_data.get("token", "").strip()
        if token:
            return token
        if self.instance.pk:
            return Bot.objects.only("token").get(pk=self.instance.pk).token
        raise forms.ValidationError("Введите токен бота.")

    def save(self, commit=True):
        self.instance.name = self.cleaned_data["bot_name"]
        return super().save(commit=commit)

    def clean_available_plugins(self):
        selected = self.cleaned_data["available_plugins"]
        if self.instance.pk:
            installed = self.instance.plugins.values_list("plugin_id", flat=True)
            if set(installed) - set(selected.values_list("pk", flat=True)):
                raise forms.ValidationError("Сначала удалите подключённые модули, которые хотите убрать из доступных.")
        return selected


class PluginConfigForm(forms.Form):
    def __init__(self, *args, bot_plugin: BotPlugin, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot_plugin = bot_plugin
        definition = bot_plugin.plugin
        merged = {**(definition.default_config or {}), **(bot_plugin.config or {})}
        for key, schema in (definition.config_schema or {}).items():
            field_type, label, value = schema.get("type"), schema.get("label", key), merged.get(key)
            if field_type == "int":
                self.fields[key] = forms.IntegerField(label=label, initial=value, required=False, min_value=schema.get("min"), max_value=schema.get("max"))
            elif field_type == "chat":
                choices = [("", "Не выбрано")] + [(str(c.chat_id), c.title or str(c.chat_id)) for c in Chat.objects.filter(platform=bot_plugin.bot.platform).order_by("title", "chat_id")]
                self.fields[key] = forms.ChoiceField(label=label, choices=choices, initial="" if value is None else str(value), required=False)
            elif field_type == "bool":
                self.fields[key] = forms.BooleanField(label=label, initial=bool(value), required=False)
            else:
                self.fields[key] = forms.CharField(label=label, initial="" if value is None else str(value), required=False, widget=forms.Textarea if schema.get("format") == "textarea" else forms.TextInput)

    def apply(self):
        result = dict(self.bot_plugin.config or {})
        for key, schema in (self.bot_plugin.plugin.config_schema or {}).items():
            value = self.cleaned_data.get(key)
            result[key] = int(value) if schema.get("type") == "chat" and value else value
        self.bot_plugin.config = result
        self.bot_plugin.save(update_fields=["config", "updated_at"])
