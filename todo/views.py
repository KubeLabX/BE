import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from course.models import Course
from todo.models import ToDo


# Create your views here.
@csrf_exempt
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def add_todo(request, course_id):
    try:
        # 교수님인 경우만
        if request.user.user_type != 't':
            return JsonResponse({"error": "Only teachers can add to-do"}, status=403)

        course = Course.objects.get(id=course_id, teacher=request.user)

        data = json.loads(request.body)
        content = data.get("content")
        if not content:
            return JsonResponse({"error": "No content"}, status=400)

        todo = ToDo.objects.create(course = course, content = content)

        return JsonResponse({
            "message": "To-Do added successfully"
        }, status=201)

        # 잘못된 형식
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found"}, status=404)
        # 서버 오류
    except Exception as e:
        return JsonResponse({"error": "Internal server error", "details": str(e)}, status=500)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def listup_todo(request, course_id):
    try:
        user = request.user
        course = Course.objects.get(id=course_id)

        if user.user_type == 't' and course.teacher != user:
            return JsonResponse({"error": "Unauthorized access"}, status=403)
        if user.user_type == 's' and user not in course.participants.all():
            return JsonResponse({"error": "You are not registered for this course"}, status=403)

        todos = ToDo.objects.filter(course=course).order_by("created_at").values(
            "id", "content", "created_at", "updated_at"
        )

        return JsonResponse({"todo_list": list(todos)}, status=200)
    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Internal server error", "details": str(e)}, status=500)