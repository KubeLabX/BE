from course.models import Course
from django.views.decorators.http import require_POST
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