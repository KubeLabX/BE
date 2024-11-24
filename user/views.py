from django.contrib.auth import login, authenticate
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import User
from django.http import JsonResponse
import json

# Create your views here.
@csrf_exempt
@require_POST
def sign_up_view(request):
    data = json.loads(request.body)

    user_type = data.get('user_type', 's')
    user_id = data.get("user_id")
    password = data.get("password")
    first_name = data.get("first_name")

    if not first_name or not user_id or not password:
        return JsonResponse({"error": "Please fill out the required fields"}, status=400)

    if user_type not in ['s', 't']:
        return JsonResponse({"error": "Invalid user type. Must be 's' (Student) or 't' (Teacher)."}, status=400)

    if User.objects.filter(user_id=user_id).exists():
        return JsonResponse({"error": "User ID already exists"}, status=400)

    user = User.objects.create_user(user_type=user_type, user_id=user_id, first_name=first_name, password=password)

    login(request, user)
    return JsonResponse({'message':'User registered successfully'}, status = 201)

@csrf_exempt
@require_POST
def login_view(request):
    data = json.loads(request.body)

    user_type = data.get('user_type')
    user_id = data.get("user_id")
    password = data.get("password")

    user = authenticate(request, user_id=user_id, password=password)

    if user is not None:
        if user.user_type != user_type:
            return JsonResponse({'error': 'Invalid user type.'}, status=400)
        login(request, user)
        return JsonResponse({'message':'login successful'}, status = 200)
    else:
        return JsonResponse({'error':'invalid credentials'}, status = 400)
