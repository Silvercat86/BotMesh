from django.contrib import admin

from bot_management.models import Bot,BotRunnerToken,PluginDefinition,PluginState

admin.site.register(Bot)
admin.site.register(BotRunnerToken)
admin.site.register(PluginDefinition)
admin.site.register(PluginState)