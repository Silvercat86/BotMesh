from django.db import models

class Event(models.Model):
    type = models.CharField(max_length=50)

    payload = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)