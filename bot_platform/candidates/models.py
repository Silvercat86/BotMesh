from django.db import models
from accounts.models import TelegramUser
from companies.models import Company

class Candidate(models.Model):
    class Status(models.TextChoices):
        NEW = "new"
        IN_REVIEW = "in_review"
        OFFER_SENT = "offer_sent"
        ACCEPTED = "accepted"
        REJECTED = "rejected"

    full_name = models.CharField(max_length=255)

    telegram_user = models.ForeignKey(TelegramUser, null=True, on_delete=models.SET_NULL)

    status = models.CharField(max_length=20, choices=Status.choices)

    company = models.ForeignKey(Company, on_delete=models.CASCADE)

class Offer(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)

    text = models.TextField()

    created_by = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True)

    is_accepted = models.BooleanField(null=True)