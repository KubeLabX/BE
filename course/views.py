from course.models import Course
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from user.models import User
from django.http import JsonResponse
from kubernetes import client, config
from practice.models import StudentPod

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
    # K8S 네임스페이스 생성
    try:
        config.load_kube_config()  # Kubernetes 클러스터 설정 로드
        v1 = client.CoreV1Api()

        namespace_manifest = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": f"course-{course.id}"
            }
        }
        v1.create_namespace(body=namespace_manifest)

    except client.exceptions.ApiException as e:
        # Kubernetes 네임스페이스 생성 실패 시 수업 삭제
        course.delete()
        return JsonResponse({"error": f"Failed to create Kubernetes namespace: {e}"}, status=500)

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

@require_POST
def register_course(request):
    if not request.user.is_authenticated or not isinstance(request.user, User):
        return JsonResponse({"error": "Unauthorized"}, status=401)
    if request.user.user_type == 't':
        return JsonResponse({"error": "Teachers cannot register for courses"}, status=403)

    code = request.POST.get('code')
    if not code:
        return JsonResponse({"error": "Code is required"}, status=400)

    try:
        course = Course.objects.get(code=code)
    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found"}, status=404)

    if course.participants.filter(id = request.user.id).exists():
        return JsonResponse({"error": "You are already registered for this course"}, status=400)

    course.participants.add(request.user)

    # Pod 생성 로직
    try:
        pod_name = f"{course.name.lower()}-{request.user.id}"
        namespace = f"course-{course.id}"

        # 이미 Pod 정보가 존재하면 그대로 사용
        if StudentPod.objects.filter(student=request.user, course=course).exists():
            return JsonResponse({"message": "You have already been assigned a Pod.", "pod_name": pod_name}, status=200)

        # Kubernetes Pod 생성
        config.load_kube_config()
        v1 = client.CoreV1Api()

        pod_manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": pod_name,
                "namespace": namespace
            },
            "spec": {
                "containers": [
                    {
                        "name": "terminal",
                        "image": "linux-terminal-image",
                        "resources": {
                            "limits": {
                                "cpu": "500m",
                                "memory": "256Mi"
                            }
                        }
                    }
                ]
            }
        }
        v1.create_namespaced_pod(namespace=namespace, body=pod_manifest)

        # DB에 Pod 정보 저장
        StudentPod.objects.create(student=request.user, course=course, pod_name=pod_name)

    except client.exceptions.ApiException as e:
        return JsonResponse({"error": f"Failed to create Pod: {e}"}, status=500)
    return JsonResponse({"message": "Course registered successfully"}, status=200)