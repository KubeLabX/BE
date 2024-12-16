from django.urls import path
from course.views import *

urlpatterns = [
    path('create/', create_course, name='create_course'),
    path('list/',list_up_courses, name='list_up_courses'),
    path('end/<int:course_id>/', end_course, name='end_course'),
    path('register/', register_course, name='register_course'),
    path('<int:course_id>', enter_course, name='enter_course'),
    path('<int:course_id>/participants/', get_course_progress, name='get_course_progress'),
    path('course/<int:course_id>/leave/', leave_course, name='leave_course'),
    path('course/<int:course_id>/drop/', drop_course, name='drop_course'),
]