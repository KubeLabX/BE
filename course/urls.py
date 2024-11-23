from django.urls import path
from course.views import create_course, list_up_courses

urlpatterns = [
    path('create/', create_course, name='create_course'),
    path('list/',list_up_courses, name='list_up_courses'),
]