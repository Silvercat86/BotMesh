from django.db.models import ProtectedError
from django.test import TestCase

from bot_management.models import Bot, BotRunner, Platform


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
