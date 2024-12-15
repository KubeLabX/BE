import json

from django.test import TestCase
from django.urls import reverse
from rest_framework_simplejwt.tokens import AccessToken

from course.models import Course
from todo.models import ToDo
from user.models import User


# Create your tests here.
class CreateToDoListTest(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            user_id=1001, first_name='Professor', password='password', user_type='t'
        )
        self.student = User.objects.create_user(user_id=1002, first_name='Student', password='password', user_type='s')
        self.course = Course.objects.create(name='Cloud', teacher=self.teacher)
        self.add_todo_url = reverse("add_todo", kwargs={"course_id": self.course.id})

        self.teacher_token = str(AccessToken.for_user(self.teacher))
        self.student_token = str(AccessToken.for_user(self.student))


    def test_t_add_todo(self):
        headers = {"HTTP_AUTHORIZATION": f"Bearer {self.teacher_token}"}
        response = self.client.post(
            self.add_todo_url,
            data=json.dumps({"content": "mkdir 명령 실행"}),
            content_type="application/json",
            **headers)
        # print("결과: ", response.json())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ToDo.objects.count(), 1)

    # 학생이 강의에 포함되어 있지 않음: 401
    # def test_fail_s_add_todo(self):
    #     headers = {"HTTP_AUTHORIZATION": f"Bearer {self.student_token}"}
    #     response = self.client.post(
    #         self.add_todo_url,
    #         data=json.dumps({"content": "교사용 기능 사용 시도"}),
    #         content_type="application/json",
    #         **headers,
    #     )
    #     print("결과: ", response.json())
    #     response = self.client.post(self.add_todo_url, {"content": "교사용 기능 사용 시도"})
    #     self.assertEqual(response.status_code, 403)


class ViewToDoListTest(TestCase):
    def setUp(self):
        # 교사와 학생 계정 생성
        self.teacher = User.objects.create_user(user_id=1001, first_name="Professor", password="password", user_type="t")
        self.student = User.objects.create_user(user_id=1002, first_name="Student", password="password", user_type="s")

        # 수업 생성 및 참가자 추가
        self.course = Course.objects.create(name="Cloud", teacher=self.teacher)
        self.course.participants.add(self.student)

        # To-Do 생성
        self.todo1 = ToDo.objects.create(course=self.course, content="Assignment 1")
        self.todo2 = ToDo.objects.create(course=self.course, content="Assignment 2")

        # URL 및 JWT 토큰 설정
        self.listup_todo_url = reverse("listup_todo", kwargs={"course_id": self.course.id})
        self.teacher_token = str(AccessToken.for_user(self.teacher))
        self.student_token = str(AccessToken.for_user(self.student))

    def test_t_view_todo(self):
        headers = {"HTTP_AUTHORIZATION": f"Bearer {self.teacher_token}"}
        response = self.client.get(self.listup_todo_url, **headers)
        print("결과: ", response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["todo_list"]), 2)

    def test_s_view_todo(self):
        headers = {"HTTP_AUTHORIZATION": f"Bearer {self.student_token}"}
        response = self.client.get(self.listup_todo_url, **headers)
        print("결과: ", response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["todo_list"]), 2)

    def test_unauthorized_access(self):
        response = self.client.get(self.listup_todo_url)
        self.assertEqual(response.status_code, 401)