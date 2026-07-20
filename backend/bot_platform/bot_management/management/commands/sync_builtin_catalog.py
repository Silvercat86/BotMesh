from django.core.management.base import BaseCommand
from django.db import transaction

from bot_management.builtin_catalog import PLUGIN_DEFINITIONS, SERVICE_DEFINITIONS
from bot_management.models import PluginDefinition, ServiceDefinition


class Command(BaseCommand):
    help = "Create or update built-in plugin and service definitions."

    @transaction.atomic
    def handle(self, *args, **options):
        services = {}
        for code, data in SERVICE_DEFINITIONS.items():
            services[code], created = ServiceDefinition.objects.update_or_create(
                code=code, defaults={**data, "is_active": True}
            )
            self.stdout.write(f"{'created' if created else 'updated'} service {code}")

        for code, data in PLUGIN_DEFINITIONS.items():
            required_codes = data["required_services"]
            defaults = {key: value for key, value in data.items() if key != "required_services"}
            definition, created = PluginDefinition.objects.update_or_create(
                code=code, defaults={**defaults, "is_active": True}
            )
            definition.required_services.set(services[item] for item in required_codes)
            self.stdout.write(f"{'created' if created else 'updated'} plugin {code}")

        self.stdout.write(self.style.SUCCESS(
            f"Synchronized {len(PLUGIN_DEFINITIONS)} plugins and {len(SERVICE_DEFINITIONS)} services."
        ))
