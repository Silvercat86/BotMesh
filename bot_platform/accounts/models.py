from django.db import models
from companies.models import Company

class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True,null = True,blank=True)

    username = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, null=True, blank=True)

    is_placeholder = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)


class Membership(models.Model):
    class Role(models.TextChoices):
        HR = "hr"
        MANAGER = "manager"
        EMPLOYEE = "employee"

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    role = models.CharField(max_length=20, choices=Role.choices)

    class Meta:
        unique_together = ("user", "company")