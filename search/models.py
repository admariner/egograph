from django.db import models

#############################################################################################################
# Search query

class Query(models.Model):
    """Parent and child queries combined into one table."""

    # Fields
    name = models.CharField(max_length=1000, unique=True) # must be unique
    date_created = models.DateTimeField(auto_now_add=True)

    # Admin naming
    class Meta:
        verbose_name = 'Query'
        verbose_name_plural = 'Queries'

    # Instance naming
    def __str__(self):
        return f"{self.name}"

#############################################################################################################
# Parent / child lookup table

class Parent_Child(models.Model):
    """Parent to child lookup table."""

    # Example related_name queries
    # query_obj.parents.all()
    # query_obj.children.count()

    # One to many relationship on Parent (delete row if Parent is deleted)
    parent = models.ForeignKey(Query, on_delete=models.CASCADE, related_name='as_parent')
    child = models.ForeignKey(Query, on_delete=models.CASCADE, related_name='as_child')
    relevance = models.PositiveIntegerField()
    date_created = models.DateTimeField(auto_now_add=True)

    # Admin naming
    class Meta:
        verbose_name = 'Parent/Child Lookup'
        verbose_name_plural = 'Parent/Child Lookups'
        # Require unique parent/child combos
        constraints = [
            models.UniqueConstraint(fields=['parent', 'child'], name='unique_parent_child')
        ]

    # Instance naming
    def __str__(self):
        return f"{self.parent.name} - {self.child.name} - {self.relevance}"
