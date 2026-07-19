from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PluginConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BirthdayConfig(PluginConfig):
    templates: str
    storage_dir: str
    people_source: str
    hour: int = Field(default=6, ge=0, le=23)
    minute: int = Field(default=0, ge=0, le=59)
    chat_id: str | int


class WorkExperienceConfig(PluginConfig):
    templates_by_years: dict[str, str]
    storage_dir: str
    people_source: str
    hour: int = Field(default=6, ge=0, le=23)
    minute: int = Field(default=0, ge=0, le=59)
    chat_id: str | int


class March8Config(PluginConfig):
    template: str
    storage_dir: str
    photo: str | None = None
    hour: int = Field(default=6, ge=0, le=23)
    minute: int = Field(default=0, ge=0, le=59)
    chat_id: str | int


class EmployeeInfoConfig(PluginConfig):
    sources: list[str] = Field(default_factory=list)
    available_nicknames: list[str] = Field(default_factory=list)
    available_chats: list[str] = Field(default_factory=list)
    scope_chats: list[int] = Field(default_factory=list)


class WelcomeConfig(PluginConfig):
    base_template: str = ""
    questions: list[str] = Field(default_factory=list)
    n_questions: int = Field(default=3, ge=0)
    dedupe_ttl_seconds: int = Field(default=30, ge=0)


class StartConfig(PluginConfig):
    messages: list[str] = Field(default_factory=list)


class ComplimentConfig(PluginConfig):
    messages: list[str] = Field(default_factory=list)


class MemeConfig(PluginConfig):
    data_file: str = "data/memes/memes.txt"


class CleverShmaConfig(PluginConfig):
    api_url: str = "https://openrouter.ai/api/v1/chat/completions"
    model: str = "deepseek/deepseek-chat"
    system_prompt: str | None = None
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=1024, gt=0)
    timeout_seconds: float = Field(default=60, gt=0)


class PeopleDirectoryConfig(PluginConfig):
    sources: dict[str, dict] = Field(default_factory=dict)
    cache_ttl: int = Field(default=300, gt=0)


def _canonical_property(schema: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "type",
        "anyOf",
        "items",
        "additionalProperties",
        "minimum",
        "maximum",
        "minLength",
        "maxLength",
        "enum",
    )
    result = {key: schema[key] for key in keys if key in schema}
    if "anyOf" in result:
        result["anyOf"] = [_canonical_property(item) for item in result["anyOf"]]
    if isinstance(result.get("items"), dict):
        result["items"] = _canonical_property(result["items"])
    if isinstance(result.get("additionalProperties"), dict):
        result["additionalProperties"] = _canonical_property(result["additionalProperties"])
    return result


def model_contract(model: type[PluginConfig]) -> dict[str, Any]:
    schema = model.model_json_schema()
    required = set(schema.get("required", []))
    return {
        "fields": {
            name: {
                **_canonical_property(field_schema),
                "required": name in required,
            }
            for name, field_schema in sorted(schema.get("properties", {}).items())
        },
        "additional_fields": schema.get("additionalProperties", True),
    }


def get_plugin_contracts(plugin_registry: dict) -> dict[str, dict[str, Any]]:
    contracts = {}
    for name, plugin_class in sorted(plugin_registry.items()):
        model = getattr(plugin_class, "config_model", None)
        if model is None:
            raise RuntimeError(f"Plugin {name} has no config_model")
        contracts[name] = {
            "config": model_contract(model),
            "required_services": sorted(getattr(plugin_class, "required_services", ())),
            "actions": getattr(plugin_class, "action_contracts", {}),
        }
    return contracts


def get_service_contracts(service_registry: dict) -> dict[str, dict[str, Any]]:
    contracts = {}
    for name, service_class in sorted(service_registry.items()):
        model = getattr(service_class, "config_model", None)
        if model is None:
            raise RuntimeError(f"Service {name} has no config_model")
        contracts[name] = model_contract(model)
    return contracts


def validate_plugin_config(plugin_class: type, config: dict[str, Any]) -> None:
    model = plugin_class.config_model
    model.model_validate(config)


def validate_service_config(service_class: type, config: dict[str, Any]) -> None:
    service_class.config_model.model_validate(config)
