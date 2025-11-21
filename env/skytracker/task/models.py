from django.db import models
import os
import datetime
from django.contrib.auth.models import User
from django.apps import apps
from django.core.exceptions import ValidationError
from django.utils import timezone

# ---------------- User -----------------
class Master_User(models.Model):
    u_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='master_user')
    user_mob = models.BigIntegerField(null=True, blank=True, unique=True)
    user_name = models.CharField(max_length=100)
    user_type = models.IntegerField(null=True, blank=True)
    email_id = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=100)
    status = models.BooleanField(default=True)
    added_by = models.IntegerField(null=True, blank=True)
    added_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    eby = models.IntegerField(null=True, blank=True)
    eat = models.DateTimeField(auto_now=True, null=True , blank=True)

    def __str__(self):
        return f"{self.user_name}"
    

class Master_Project(models.Model):
    project_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(Master_User, on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('owner', 'name')

    def __str__(self):
        return self.name
    

class Master_Task(models.Model):
    STATUS_CHOICES = [ ('todo', 'To Do'), ('in_progress', 'In Progress'), ('done', 'Done')]
    task_id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Master_Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='todo')
    priority = models.IntegerField()
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assignee = models.ForeignKey(Master_User, null=True, blank=True, on_delete=models.SET_NULL, related_name='tasks_assigned')

    def clean(self):
        if not (1 <= self.priority <= 5):
            raise ValidationError("Priority must be between 1 (highest) and 5 (lowest).")
        if self.status == "done" and self.due_date and self.due_date > timezone.now().date():
            raise ValidationError("Done tasks cannot have a future due date.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)