from django.db import models
from django.contrib.auth.models import User

class Task(models.Model):
    class Priority(models.TextChoices):
        HIGH = 'high', 'High'
        MEDIUM = 'medium', 'Medium'  
        LOW = 'low', 'Low'
        
    class Status(models.TextChoices):
        COMPLETED = 'completed', 'Completed'
        IN_PROGRESS = 'in_progress', 'In Progress'
        PENDING = 'pending', 'Pending'
    
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.LOW)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.title} by: {self.user.username}"
    
