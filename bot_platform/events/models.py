from django.db import models

class Event(models.Model):
    type = models.CharField(max_length=50)

    payload = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)

    entity_type = models.CharField(max_length=50, null=True, blank=True)
    entity_id = models.IntegerField(null=True, blank=True)  

    class Meta:
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["created_at"]),
        ]