from django.db import models
from accounts.models import TelegramUser
from companies.models import Company

class Candidate(models.Model):
    

    full_name = models.CharField(max_length=255)

    telegram_user = models.ForeignKey(TelegramUser, null=True, on_delete=models.SET_NULL)

    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "telegram_user"],
                name="unique_candidate_per_company_telegram_user",
            ),
        ]



class Offer(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft"
        SENT = "sent"
        ACCEPTED = "accepted"
        DISCUSS = "discuss"
        REJECTED = "rejected"
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)

    employee = models.OneToOneField(
        "Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="offer",
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    text = models.TextField()

    created_by = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    status = models.CharField(max_length=20,choices=Status.choices)

class OfferResponse(models.Model):
    class Type(models.TextChoices):
        ACCEPT = "accept"
        DISCUSS = "discuss"
        REJECT = "reject"

    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)

    type = models.CharField(max_length=20, choices=Type.choices)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("offer","type")


class Employee(models.Model):
    full_name = models.CharField(max_length=255)

    telegram_user = models.OneToOneField(
        TelegramUser, null=True, blank=True, on_delete=models.SET_NULL
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    manager = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)

    birthday = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)

    external_id = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "telegram_user"],
                name="unique_employee_per_company_telegram_user",
            ),
        ]
