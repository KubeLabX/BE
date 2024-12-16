from django.db import models

from course.models import Course
from user.models import User


# Create your models here.
class ToDo(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="todo_items")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # deadline = models.DateTimeField()
    completed_by = models.ManyToManyField(User, related_name="completed_todos", blank=True)

    def __str__(self):
        return self.content
        # return f"{self.content[:50]} (Course: {self.course.name})" 라고 해야 하나?