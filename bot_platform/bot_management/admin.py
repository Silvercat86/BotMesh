from django.contrib import admin

from bot_management.models import Bot, BotAccess, BotPlugin, BotRunner, PluginDefinition, PluginState

admin.site.register(Bot)
admin.site.register(BotRunner)
admin.site.register(PluginDefinition)
admin.site.register(PluginState)
admin.site.register(BotAccess)
admin.site.register(BotPlugin)
