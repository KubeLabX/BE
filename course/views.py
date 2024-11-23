from course.models import Course
from django.views.decorators.http import require_POST, require_GET
from user.models import User
from django.http import JsonResponse


# Create your views here.
@require_POST
def create_course(request):
    if not request.user.is_authenticated or not isinstance(request.user, User):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.user.user_type != 't':
        return JsonResponse({"error": "Only teachers can create courses"}, status=403)

    name = request.POST.get('name')
    if not name:
        return JsonResponse({"error": "Name is required"}, status=400)

    course = Course.objects.create(name=name, teacher=request.user)

    return JsonResponse({"message": "Course created successfully"}, status=201)

@require_GET
def list_up_courses(request):
    if not request.user.is_authenticated or not isinstance(request.user, User):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    if request.user.user_type == 't':
        courses = Course.objects.filter(teacher=request.user)
        course_data = [
            {
                'name': c.name,
                'participant_count': c.participants.count(),
                'created_at': c.created_at,
            }
            for c in courses
        ]
        return JsonResponse({"courses": course_data}, status=200)

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