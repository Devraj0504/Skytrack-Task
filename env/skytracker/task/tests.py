from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q
from datetime import date, timedelta

from task.models import Master_User, Master_Project, Master_Task


class ProjectTaskTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass123")

        self.master1 = Master_User.objects.create(
            user=self.user1,
            user_name="User One",
            email_id="user1@example.com",
            password="pass123",
            status=True
        )
        self.master2 = Master_User.objects.create(
            user=self.user2,
            user_name="User Two",
            email_id="user2@example.com",
            password="pass123",
            status=True
        )

        self.project1 = Master_Project.objects.create(
            name="Project A",
            owner=self.master1
        )

        self.task1 = Master_Task.objects.create(
            project=self.project1,
            title="Task 1",
            priority=3,
            status="todo",
            assignee=self.master1
        )

    def test_duplicate_project_name_not_allowed(self):
        with self.assertRaises(IntegrityError):
            Master_Project.objects.create(
                name="Project A",
                owner=self.master1
            )

    def test_done_task_cannot_have_future_due_date(self):
        future_date = date.today() + timedelta(days=5)
        task = Master_Task(
            project=self.project1,
            title="Future Task",
            priority=2,
            status="done",
            due_date=future_date,
            assignee=self.master1
        )
        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_task_visibility_via_orm(self):
        other_project = Master_Project.objects.create(
            name="Other Project",
            owner=self.master2
        )

        Master_Task.objects.create(
            project=other_project,
            title="Hidden Task",
            priority=4,
            assignee=self.master2
        )

        Master_Task.objects.create(
            project=other_project,
            title="Assigned To User1",
            priority=2,
            assignee=self.master1
        )

        visible_qs = Master_Task.objects.filter(
            Q(project__owner=self.master1) | Q(assignee=self.master1)
        )

        titles = set(visible_qs.values_list('title', flat=True))

        self.assertIn("Task 1", titles)
        self.assertIn("Assigned To User1", titles)
        self.assertNotIn("Hidden Task", titles)
