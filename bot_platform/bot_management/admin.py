from django.contrib import admin

from bot_management.models import (
    Bot, BotAccess, BotAction, BotPlugin, BotRunner, BotService,
    PluginDefinition, PluginState, ServiceDefinition,
)

admin.site.register(Bot)
admin.site.register(BotRunner)
admin.site.register(PluginDefinition)
admin.site.register(PluginState)
admin.site.register(BotAccess)
admin.site.register(BotPlugin)
admin.site.register(ServiceDefinition)
admin.site.register(BotService)
admin.site.register(BotAction)
