from django.db import models

#############################################################################################################
# Nodes

class Node(models.Model):
    """Parent and child nodes."""

    # Fields
    name = models.CharField(max_length=1000, unique=True) # must be unique
    date_created = models.DateTimeField(auto_now_add=True)

    # Admin naming
    class Meta:
        verbose_name = 'Node'
        verbose_name_plural = 'Nodes'

    # Instance naming
    def __str__(self):
        return f"{self.id} - {self.name}"

#############################################################################################################
# Edges

class Edge(models.Model):
    """Parent to child edges."""

    # Example related_name queries
    # query_obj.parents.all()
    # query_obj.children.count()

    # One to many relationship on Parent (delete row if Parent is deleted)
    parent = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='as_parent')
    child = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='as_child')
    weight = models.PositiveIntegerField()
    date_created = models.DateTimeField(auto_now_add=True)

    # Admin naming
    class Meta:
        verbose_name = 'Edge'
        verbose_name_plural = 'Edges'
        # Require unique edges
        constraints = [
            models.UniqueConstraint(fields=['parent', 'child'], name='unique_edge')
        ]

    # Instance naming
    def __str__(self):
        return f"{self.id} - {self.parent.name} - {self.child.name} - weight:{self.weight}"
