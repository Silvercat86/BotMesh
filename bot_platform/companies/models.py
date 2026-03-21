from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255)

    timezone = models.CharField(max_length=64)
    working_hours_start = models.TimeField()
    working_hours_end = models.TimeField()

    def __str__(self):
        return f'{self.name} ({self.timezone})'