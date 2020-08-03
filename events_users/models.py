from django.db import models
from django.contrib.auth.models import User


class Event(models.Model):
    title = models.CharField(max_length=256)
    description = models.TextField()
    date = models.DateTimeField()
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='creator'
    )
    users = models.ManyToManyField(User, related_name='event_attendees')

