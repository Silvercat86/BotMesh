from django.contrib import admin

from .models import TelegramUser,Membership

admin.site.register(TelegramUser)
admin.site.register(Membership)

