from django.contrib import admin

from .models import Chat,ChatMembership,Template,Notification

admin.site.register(Chat)
admin.site.register(ChatMembership)
admin.site.register(Template)
admin.site.register(Notification)
