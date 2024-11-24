import json
from django.views.decorators.csrf import csrf_exempt
from course.models import Course
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from user.models import User
from django.http import JsonResponse


# Create your views here.
@csrf_exempt
@require_POST
def create_course(request):
    if not request.user.is_authenticated or not isinstance(request.user, User):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.user.user_type != 't':
        return JsonResponse({"error": "Only teachers can create courses"}, status=403)

    name = json.loads(request.body)
    if not name:
        return JsonResponse({"error": "Name is required"}, status=400)

    course = Course.objects.create(name=name, teacher=request.user)

    return JsonResponse({"message": "Course created successfully"}, status=201)

@csrf_exempt
@require_GET
def list_up_courses(request):
    user = request.user
    if not user.is_authenticated or not isinstance(request.user, User):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    if user.user_type == 't':
        courses = Course.objects.filter(teacher=request.user)
        course_data = [
            {
                "id": c.id,
                'name': c.name,
                'participant_count': c.participants.count(),
                'created_at': c.created_at,
            }
            for c in courses
        ]
        return JsonResponse({"courses": course_data, "name": user.first_name, "role": user.user_type}, status=200)

    if request.user.user_type == 's':
        courses = Course.objects.filter(participants=request.user)
        course_data = [
            {
                'name': c.name,
                'teacher_name': c.teacher.first_name,
                'created_at': c.created_at,
            }
            for c in courses
        ]
        return JsonResponse({"courses": course_data}, status=200)

@csrf_exempt
@require_http_methods(['DELETE'])
def end_course(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found"}, status=404)

    if course.teacher != request.user:
        return JsonResponse({"error": "Only the teacher can end this course"}, status=403)

    course.delete()
    return JsonResponse({"message": "Course ended successfully"}, status=200)

@csrf_exempt
@require_POST
def register_course(request):
    if not request.user.is_authenticated or not isinstance(request.user, User):
        return JsonResponse({"error": "Unauthorized"}, status=401)
    if request.user.user_type == 't':
        return JsonResponse({"error": "Teachers cannot register for courses"}, status=403)

    code = json.loads(request.body)
    if not code:
        return JsonResponse({"error": "Code is required"}, status=400)

    try:
        course = Course.objects.get(code=code)
    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found"}, status=404)

    if course.participants.filter(id = request.user.id).exists():
        return JsonResponse({"error": "You are already registered for this course"}, status=400)

    course.participants.add(request.user)
    return JsonResponse({"message": "Course registered successfully"}, status=200)