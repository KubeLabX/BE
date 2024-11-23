from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, user_id, first_name, password=None, **extra_fields):
        if not user_id:
            raise ValueError("The User must have a user_id")
        user = self.model(user_id=user_id, first_name=first_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_id, first_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(user_id, first_name, password, **extra_fields)

class User(AbstractUser):
    USER_TYPE_CHOICES = (('s', 'Student'), ('t', 'Teacher'))

    user_type = models.CharField(max_length=1, choices=USER_TYPE_CHOICES, default='s')
    user_id = models.PositiveIntegerField(unique=True, null=False, blank=False)
    username = None
    first_name = models.CharField(max_length=30, null=False, blank=False)

    USERNAME_FIELD = 'user_id'
    REQUIRED_FIELDS = ['first_name']

    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} ({self.get_user_type_display()})"