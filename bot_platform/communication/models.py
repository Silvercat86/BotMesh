from django.db import models
from companies.models import Company

class Chat(models.Model):
    telegram_id = models.BigIntegerField(unique=True)

    type = models.CharField(max_length=20,choices={"private":"Private chat","group":"Group chat"})
    title = models.CharField(max_length=255, null=True, blank=True)

    company = models.ForeignKey(Company, null=True, on_delete=models.SET_NULL)