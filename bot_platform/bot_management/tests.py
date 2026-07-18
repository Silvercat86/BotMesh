from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from bot_management.models import Bot, BotAccess, BotPlugin, BotRunner, Platform, PluginDefinition


class BotModelTests(TestCase):
    def setUp(self):
        self.runner = BotRunner.objects.create(
            name="runner-one",
            api_key="runner-key",
            is_active=True,
        )

    def create_bot(self, **overrides):
        data = {
            "name": "test-bot",
            "platform": Platform.TELEGRAM,
            "runner": self.runner,
            "token": "bot-token",
            "api_key": "bot-api-key",
        }
        data.update(overrides)
        return Bot.objects.create(**data)

    def test_new_bot_starts_at_version_one(self):
        bot = self.create_bot()

        self.assertEqual(bot.version, 1)

    def test_api_key_is_generated_when_omitted(self):
        bot = Bot.objects.create(
            name="generated-key-bot",
            platform=Platform.TELEGRAM,
            runner=self.runner,
            token="bot-token",
        )

        self.assertTrue(bot.api_key.startswith("bot_"))

    def test_saving_existing_bot_increments_version(self):
        bot = self.create_bot()

        bot.save()

        bot.refresh_from_db()
        self.assertEqual(bot.version, 2)

    def test_partial_update_persists_incremented_version(self):
        bot = self.create_bot()

        bot.is_active = True
        bot.save(update_fields=["is_active"])

        bot.refresh_from_db()
        self.assertTrue(bot.is_active)
        self.assertEqual(bot.version, 2)

    def test_runner_with_assigned_bots_cannot_be_deleted(self):
        self.create_bot()

        with self.assertRaises(ProtectedError):
            self.runner.delete()


class BotPluginTests(TestCase):
    def setUp(self):
        self.bot = Bot.objects.create(name="bot", platform=Platform.TELEGRAM, token="token", api_key="key")
        self.plugin = PluginDefinition.objects.create(code="welcome", title="Welcome", default_config={"text": "Hello"})

    def test_only_available_plugin_can_be_installed(self):
        with self.assertRaises(ValidationError):
            BotPlugin.objects.create(bot=self.bot, plugin=self.plugin)

    def test_plugin_change_increments_bot_version(self):
        self.bot.available_plugins.add(self.plugin)
        item = BotPlugin.objects.create(bot=self.bot, plugin=self.plugin, config={"text": "Hi"})
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.version, 2)
        item.is_enabled = True
        item.save()
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.version, 3)


class DashboardAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="operator", password="pass")
        self.viewer = User.objects.create_user(username="viewer", password="pass")
        self.superuser = User.objects.create_superuser(username="root", password="pass", email="root@example.com")
        self.bot = Bot.objects.create(name="bot", platform=Platform.TELEGRAM, token="token", api_key="key")
        BotAccess.objects.create(user=self.user, bot=self.bot, role=BotAccess.Role.OPERATOR)
        BotAccess.objects.create(user=self.viewer, bot=self.bot, role=BotAccess.Role.VIEWER)

    def test_user_sees_assigned_bot(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard_bot_list"))
        self.assertContains(response, self.bot.name)

    def test_viewer_cannot_toggle_bot(self):
        self.client.force_login(self.viewer)
        response = self.client.post(reverse("dashboard_toggle_bot", args=[self.bot.pk]))
        self.assertEqual(response.status_code, 403)

    def test_operator_can_toggle_bot(self):
        self.client.force_login(self.user)
        self.client.post(reverse("dashboard_toggle_bot", args=[self.bot.pk]))
        self.bot.refresh_from_db()
        self.assertTrue(self.bot.is_active)

    def test_only_superuser_can_open_bot_creation(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("dashboard_bot_create")).status_code, 403)
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("dashboard_bot_create"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'type="password"')
        self.assertContains(response, 'name="bot_name"')
