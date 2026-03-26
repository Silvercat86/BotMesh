from django.contrib import admin

from .models import Chat,Bot,ChatMembership,BotSession,Template,Notification

admin.site.register(Chat)
admin.site.register(Bot)
admin.site.register(ChatMembership)
admin.site.register(BotSession)
admin.site.register(Template)
admin.site.register(Notification)
