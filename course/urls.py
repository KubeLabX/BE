from django.urls import path
from course.views import create_course, list_up_courses, end_course, register_course, enter_course

urlpatterns = [
    path('create/', create_course, name='create_course'),
    path('list/',list_up_courses, name='list_up_courses'),
    path('end/<int:course_id>/', end_course, name='end_course'),
    path('register/', register_course, name='register_course'),
    path('<int:course_id>', enter_course, name='enter_course'),
]