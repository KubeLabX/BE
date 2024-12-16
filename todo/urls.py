from django.urls import path
from .views import add_todo, listup_todo

urlpatterns = [
    path("course/<int:course_id>/add", add_todo, name="add_todo"),
    path("course/<int:course_id>/list", listup_todo, name="listup_todo")
]