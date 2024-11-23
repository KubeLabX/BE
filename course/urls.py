from django.urls import path
from course.views import create_course, list_up_courses, end_course

urlpatterns = [
    path('create/', create_course, name='create_course'),
    path('list/',list_up_courses, name='list_up_courses'),
    path('end/<int:course_id>/', end_course, name='end_course'),
]