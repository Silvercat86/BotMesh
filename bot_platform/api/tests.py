from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from bot_management.models import Bot, BotRunner, Platform, PluginState


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
