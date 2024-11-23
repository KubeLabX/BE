from django.urls import path
from course.views import create_course

urlpatterns = [
    path('create/', create_course, name='create_course'),
]