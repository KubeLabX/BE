from django.test import TestCase
from django.urls import reverse
from course.models import Course
from user.models import User


# Create your tests here.
class CourseCreateTest(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            user_id=1001, first_name='Professor', password='password', user_type='t'
        )
        self.student = User.objects.create_user(
            user_id=9009, first_name='Student', password='password', user_type='s'
        )
        self.create_course_url = reverse('create_course')

    def test_create_course(self):
        self.client.login(user_id=self.teacher.user_id, password='password')
        response = self.client.post(self.create_course_url, {'name': 'Cloud'})

        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(Course.objects.first().name, 'Cloud')
        self.assertEqual(len(Course.objects.first().code), 6)

        self.assertEqual(response.status_code, 201)

    def test_fail_student_create_course(self):
        self.client.login(user_id=self.student.user_id, password='password')
        response = self.client.post(self.create_course_url, {'name': 'Cloud'})
        self.assertEqual(response.status_code, 403)

    def test_fail_form_unfilled(self):
        self.client.login(user_id=self.teacher.user_id, password='password')
        response = self.client.post(self.create_course_url, {})
        self.assertEqual(Course.objects.count(), 0)

        self.assertEqual(response.status_code, 400)
