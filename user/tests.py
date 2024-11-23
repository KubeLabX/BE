from django.test import TestCase
from django.urls import reverse
from .models import User


class SignupTest(TestCase):
    def test_signup_success(self):
        # 회원가입 요청
        response = self.client.post(reverse('signup'), {
            'user_id': 1234567,
            'password': 'testpassword',
            'first_name': 'TestUser',
            'user_type': 's'
        })

        # 성공 응답 검증
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['message'], 'User registered successfully')

        # 데이터베이스에 저장 확인
        user = User.objects.filter(user_id=1234567).first()
        self.assertIsNotNone(user)
        self.assertEqual(user.first_name, 'TestUser')
        self.assertEqual(user.user_type, 's')

    def test_signup_missing_field(self):
        # 필수 필드 누락
        response = self.client.post(reverse('signup'), {
            'user_id': 1234567,
            'password': 'testpassword',
        })

        # 실패 응답 검증
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Please fill out the required fields')
