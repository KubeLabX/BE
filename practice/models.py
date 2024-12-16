from django.db import models
from user.models import User
from course.models import Course

class StudentPod(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pods')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='pods')
    pod_name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')  # 학생과 수업의 조합은 고유해야 함

    def __str__(self):
        return f"{self.student.first_name} - {self.course.name} - {self.pod_name}"
