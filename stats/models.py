from django.db import models

#############################################################################################################
# Stats

class Stat(models.Model):
    """Parent and child nodes."""

    # Fields
    name = models.CharField(max_length=1000, unique=True) # must be unique
    data = models.JSONField(null=True, blank=True)
    date_updated = models.DateTimeField(auto_now=True) # updates every time it is saved

    # Admin naming
    class Meta:
        verbose_name = 'Stat'
        verbose_name_plural = 'Stats'

    # Instance naming
    def __str__(self):
        return f"{self.name} - {self.date_updated}"



