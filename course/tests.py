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

class CourseListUpTest(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            user_id=1001, first_name='Professor', password='password', user_type='t'
        )
        self.teacher2 = User.objects.create_user(
            user_id=1002, first_name='Prof2', password='password', user_type='t'
        )
        self.student = User.objects.create_user(
            user_id=9009, first_name='Student', password='password', user_type='s'
        )
        self.student2 = User.objects.create_user(
            user_id=9008, first_name='Stud2', password='password', user_type='s'
        )

        self.course1 = Course.objects.create(name='Cloud', teacher=self.teacher)
        self.course2 = Course.objects.create(name='Python', teacher=self.teacher2)

        self.course1.participants.add(self.student, self.student2)
        self.course2.participants.add(self.student)
        self.list_up_course_url = reverse('list_up_courses')

    def test_list_up_course_t(self):
        self.client.login(user_id=self.teacher.user_id, password='password')
        response = self.client.get(self.list_up_course_url)
        response_data = response.json()["courses"]

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['name'], 'Cloud')
        self.assertEqual(response_data[0]['participant_count'], 2)
        self.assertIn('created_at', response_data[0])

        self.assertEqual(response.status_code, 200)

    def test_list_up_course_s(self):
        self.client.login(user_id=self.student.user_id, password='password')
        response = self.client.get(self.list_up_course_url)
        response_data = response.json()["courses"]

        self.assertEqual(len(response_data), 2)
        self.assertEqual(response_data[0]['name'], 'Cloud')
        self.assertEqual(response_data[0]['teacher_name'], 'Professor')
        self.assertIn('created_at',response_data[0])

        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user(self):
        response = self.client.get(self.list_up_course_url)
        self.assertEqual(response.status_code, 403)