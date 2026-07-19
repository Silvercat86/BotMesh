from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from bot_management.models import (
    Bot, BotAction, BotPlugin, BotRunner, BotService, Platform,
    PluginDefinition, PluginState, ServiceDefinition,
)


class ApiAuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.runner = BotRunner.objects.create(
            name="runner-one",
            api_key="runner-key-without-required-prefix",
            is_active=True,
        )
        self.bot = Bot.objects.create(
            name="test-bot",
            platform=Platform.TELEGRAM,
            runner=self.runner,
            token="token",
            api_key="bot-key",
            is_active=True,
        )

    def test_api_key_is_required(self):
        response = self.client.get(reverse("get_active_bots"))

        self.assertEqual(response.status_code, 403)

    def test_runner_key_only_accesses_runner_endpoint(self):
        response = self.client.get(
            reverse("load_plugin_state"),
            {"plugin": "start_plugin"},
            HTTP_X_API_KEY=self.runner.api_key,
        )

        self.assertEqual(response.status_code, 403)

    def test_bot_key_cannot_access_runner_endpoint(self):
        response = self.client.get(
            reverse("get_active_bots"),
            HTTP_X_API_KEY=self.bot.api_key,
        )

        self.assertEqual(response.status_code, 403)


class RunnerContractApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.runner = BotRunner.objects.create(
            name="contract-runner",
            api_key="contract-runner-key",
            is_active=True,
        )
        self.contract = {
            "fields": {
                "message": {"type": "string", "required": True},
            },
            "additional_fields": False,
        }
        self.service_contract = {
            "fields": {
                "cache_ttl": {"type": "integer", "required": False},
                "sources": {
                    "type": "object",
                    "additionalProperties": {"type": "object", "additionalProperties": True},
                    "required": False,
                },
            },
            "additional_fields": False,
        }
        PluginDefinition.objects.create(
            code="message_plugin",
            title="Message",
            runtime_schema=self.contract,
        )

    def validate(self, plugins):
        return self.client.post(
            reverse("validate_runner_contracts"),
            {"plugins": plugins, "services": {"people_directory_service": self.service_contract}},
            format="json",
            HTTP_X_API_KEY=self.runner.api_key,
        )

    def test_matching_contract_is_compatible(self):
        response = self.validate({"message_plugin": {
            "config": self.contract, "required_services": [], "actions": {},
        }})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "compatible", "errors": []})

    def test_missing_plugin_is_reported(self):
        response = self.validate({})

        self.assertEqual(response.json()["status"], "incompatible")
        self.assertEqual(
            response.json()["errors"],
            [{"type": "missing_plugin", "plugin": "message_plugin", "expected": {
                "config": self.contract, "required_services": [], "actions": {},
            }}],
        )

    def test_field_difference_contains_expected_and_actual_contracts(self):
        actual = {
            "fields": {
                "message": {"type": "integer", "required": True},
            },
            "additional_fields": False,
        }

        response = self.validate({"message_plugin": {
            "config": actual, "required_services": [], "actions": {},
        }})
        error = response.json()["errors"][0]

        self.assertEqual(error["type"], "field_contract_mismatch")
        self.assertEqual(error["plugin"], "message_plugin")
        self.assertEqual(error["field"], "message")
        self.assertEqual(error["expected"]["type"], "string")
        self.assertEqual(error["actual"]["type"], "integer")

    def test_bot_key_cannot_validate_runner_contracts(self):
        bot = Bot.objects.create(
            name="contract-bot",
            platform=Platform.TELEGRAM,
            token="token",
            is_active=True,
        )
        response = self.client.post(
            reverse("validate_runner_contracts"),
            {"plugins": {}, "services": {}},
            format="json",
            HTTP_X_API_KEY=bot.api_key,
        )

        self.assertEqual(response.status_code, 403)


class ActiveBotsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.runner = BotRunner.objects.create(
            name="runner-one",
            api_key="runner-one-key",
            is_active=True,
        )
        self.other_runner = BotRunner.objects.create(
            name="runner-two",
            api_key="runner-two-key",
            is_active=True,
        )

    def create_bot(self, name, runner, *, is_active=True):
        return Bot.objects.create(
            name=name,
            platform=Platform.TELEGRAM,
            runner=runner,
            token=f"{name}-token",
            api_key=f"{name}-key",
            is_active=is_active,
        )

    def test_runner_receives_only_its_active_bots(self):
        own_bot = self.create_bot("own", self.runner)
        self.create_bot("other", self.other_runner)
        self.create_bot("inactive", self.runner, is_active=False)
        self.create_bot("unassigned", None)

        response = self.client.get(
            reverse("get_active_bots"),
            HTTP_X_API_KEY=self.runner.api_key,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [bot["name"] for bot in response.json()["active_bots"]],
            [own_bot.name],
        )

    def test_runner_receives_only_enabled_installed_plugins(self):
        bot = self.create_bot("plugins", self.runner)
        enabled = PluginDefinition.objects.create(code="enabled", title="Enabled")
        disabled = PluginDefinition.objects.create(code="disabled", title="Disabled")
        bot.available_plugins.add(enabled, disabled)
        BotPlugin.objects.create(bot=bot, plugin=enabled, is_enabled=True, config={"text": "hello"})
        BotPlugin.objects.create(bot=bot, plugin=disabled, is_enabled=False)

        response = self.client.get(reverse("get_active_bots"), HTTP_X_API_KEY=self.runner.api_key)
        payload = next(item for item in response.json()["active_bots"] if item["name"] == bot.name)
        self.assertEqual(payload["plugins"], [{"name": "enabled", "text": "hello"}])

    def test_runner_receives_relational_services_and_exact_plugin_actions(self):
        bot = self.create_bot("relations", self.runner)
        service = ServiceDefinition.objects.create(code="directory", title="Directory")
        BotService.objects.create(bot=bot, service=service, is_enabled=True, config={"cache_ttl": 60})
        plugin = PluginDefinition.objects.create(
            code="commands", title="Commands",
            actions_schema={"hello": {"types": ["command"]}},
        )
        bot.available_plugins.add(plugin)
        bot_plugin = BotPlugin.objects.create(bot=bot, plugin=plugin, is_enabled=True)
        BotAction.objects.create(
            bot=bot, plugin=bot_plugin, name="hello", handler="hello", type="command"
        )

        response = self.client.get(reverse("get_active_bots"), HTTP_X_API_KEY=self.runner.api_key)
        payload = next(item for item in response.json()["active_bots"] if item["name"] == bot.name)

        self.assertEqual(payload["services"], [{"name": "directory", "cache_ttl": 60}])
        self.assertEqual(payload["actions"][0]["plugin"], "commands")
        self.assertEqual(payload["actions"][0]["func_name"], "hello")


class PluginStateApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.bot = Bot.objects.create(
            name="state-bot",
            platform=Platform.TELEGRAM,
            token="token",
            api_key="state-bot-key",
            is_active=True,
        )

    def save_state(self, state):
        return self.client.post(
            reverse("save_plugin_state"),
            {"plugin": "birthday_plugin", "state": state},
            format="json",
            HTTP_X_API_KEY=self.bot.api_key,
        )

    def test_save_state_updates_only_provided_keys(self):
        self.save_state({"last_run": "2026-07-15", "image": 2})

        response = self.save_state({"last_run": "2026-07-16"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["state"],
            {"last_run": "2026-07-16", "image": 2},
        )

    def test_state_must_be_an_object(self):
        response = self.save_state(["invalid"])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "state must be an object")

    def test_empty_state_keeps_existing_plugin_state(self):
        self.save_state({"last_run": "2026-07-15"})

        response = self.save_state({})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["state"], {"last_run": "2026-07-15"})
        self.assertTrue(PluginState.objects.filter(bot=self.bot).exists())
