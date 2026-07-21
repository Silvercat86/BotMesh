import os

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from bot_management.models import BotRunner


class Command(BaseCommand):
    help = "Create or update an active BotRunner using an API key from an environment variable."

    def add_arguments(self, parser):
        parser.add_argument("--name", default="local-runner")
        parser.add_argument("--key-env", default="BOT_RUNNER_API_KEY")

    def handle(self, *args, **options):
        variable = options["key_env"]
        api_key = os.getenv(variable, "").strip()
        if not api_key:
            raise CommandError(f"{variable} is empty or unavailable")

        runner = BotRunner.objects.filter(api_key=api_key).first()
        if runner:
            created = False
            if not runner.is_active:
                runner.is_active = True
                runner.save(update_fields=["is_active"])
        else:
            try:
                runner, created = BotRunner.objects.update_or_create(
                    name=options["name"],
                    defaults={"api_key": api_key, "is_active": True},
                )
            except IntegrityError as exc:
                raise CommandError("Runner name and API key belong to different records") from exc

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} active runner: {runner.name}"))
