import json, logging
from django.views.decorators.csrf import csrf_exempt
from kubernetes.client import ApiException
from course.models import Course
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from kubernetes import client, config
from practice.models import StudentPod

logger = logging.getLogger(__name__)

@csrf_exempt
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def create_course(request):
    try:
        if request.user.user_type != 't':
            return JsonResponse({"error": "Only teachers can create courses"}, status=403)
        
        data = json.loads(request.body)
        name = data.get('name')
        
        if not name or not name.strip():
            return JsonResponse({"error": "Course name is required"}, status=400)

        logger.info("[INFO] Creating course...")
        course = Course.objects.create(
            name=name.strip(),
            teacher=request.user
        )
        logger.info(f"[INFO] Course created with ID: {course.id}")

        # namespace 설정
        course.namespace = f"course-{course.id}"
        course.save()
        logger.info(f"[INFO] Course namespace set to: {course.namespace}")

        ##네임스페이스 생성 오류 생기는 부분분
        # try:
        #     logger.info("[INFO] Attempting to load Kubernetes configuration.")
        #     config.load_incluster_config()  # Kubernetes 클러스터 설정 로드
        #     logger.info("[INFO] Kubernetes configuration loaded successfully.")
        #     v1 = client.CoreV1Api()

        #     namespace_manifest = {
        #         "apiVersion": "v1",
        #         "kind": "Namespace",
        #         "metadata": {
        #             "name": course.namespace
        #         }
        #     }
        #     logger.info("[INFO] Namespace manifest prepared:", namespace_manifest)

        #     v1.create_namespace(body=namespace_manifest)
        #     logger.info("[INFO] Namespace created successfully for course:", course.id)


        # except client.exceptions.ApiException as e:
        #     logger.error(f"K8s API Exception: {str(e)}")  # 로그 추가
        #     # Kubernetes 네임스페이스 생성 실패 시 수업 삭제
        #     course.delete()
        #     logger.error(f"Course {course.id} deleted successfully")
        #     return JsonResponse({"error": f"Failed to create Kubernetes namespace: {e}"}, status=500)

        return JsonResponse({
            "message": "Course created successfully",
            "course_id": course.id,
            "course_name": course.name,
            "course_code": course.code
        }, status=201)

    # except client.exceptions.ApiException as e:
    #     # k8s 네임스페이스 생성 실패 시 수업 삭제
    #     course.delete()
    #     return JsonResponse({"error": f"Failed to create k8s namespace: {e}"}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    except Exception as e:
        return JsonResponse({"error": f"Internal server error: {e}"}, status=500)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def list_up_courses(request):
    try:
        user_name = request.user.first_name
        user_role = request.user.user_type

        if user_role == 't':
            courses = Course.objects.filter(teacher=request.user)
            course_data = [{
                'id': c.id,
                'name': c.name,
                'participant_count': c.participants.count(),
                'created_at': c.created_at,
            } for c in courses]

        elif user_role == 's':
            courses = Course.objects.filter(participants=request.user)
            course_data = [{
                'id': c.id,
                'name': c.name,
                'teacher_name': c.teacher.first_name,
                'created_at': c.created_at,
            } for c in courses]

        else:
            return JsonResponse({"error": "Invalid user role"}, status=400)

        return JsonResponse({
            "courses": course_data,
            "name": user_name,
            "role": user_role
        }, status=200)

    except Exception as e:
        return JsonResponse({"error": f"Failed to create Pod: {e}"}, status=500)


@csrf_exempt
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def end_course(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found"}, status=404)

    if course.teacher != request.user:
        return JsonResponse({"error": "Only the teacher can end this course"}, status=403)

    try:
        config.load_incluster_config()
        v1 = client.CoreV1Api()

        namespace_name = f"course-{course_id}"

        try:
            v1.delete_namespace(name=namespace_name)
        except ApiException as e:
            if e.status != 404:
                return JsonResponse({"error": f"Failed to delete namespace: {e.reason}"}, status=500)

    except ApiException as e:
        return JsonResponse({"error": f"Kubernetes API error: {e.reason}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Internal server error: {e}"}, status=500)

    course.delete()

    return JsonResponse({"message": "Course ended successfully"}, status=200)


@csrf_exempt
@api_view(['POST']) 
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def register_course(request):
    try:
        if request.user.user_type == 't':
            return JsonResponse({"error": "Teachers cannot register for courses"}, status=403)
        
        data = json.loads(request.body)
        code = data.get('code')
        if not code:
            return JsonResponse({"error": "Course code is required"}, status=400)

        try:
            course = Course.objects.get(code=code)
        except Course.DoesNotExist:
            return JsonResponse({"error": "Invalid course code"}, status=404)

        if course.participants.filter(id=request.user.id).exists():
            return JsonResponse({"error": "You are already registered for this course"}, status=400)
        
        course.participants.add(request.user)

        # Pod 생성 로직(미완)
        # try:
        #     pod_name = f"{course.name.lower()}-{request.user.id}"
        #     namespace = f"course-{course.id}"
        #     logger.info(f"Creating Pod: {pod_name} in namespace: {namespace}")


        #     if StudentPod.objects.filter(student=request.user, course=course).exists():
        #         return JsonResponse({"message": "You have already been assigned a Pod.", "pod_name": pod_name}, status=200)

        #     config.load_incluster_config()
        #     logger.info("Kubernetes configuration loaded.")
        #     v1 = client.CoreV1Api()
        #     pod_manifest = {
        #         "apiVersion": "v1",
        #         "kind": "Pod",
        #         "metadata": {
        #             "name": pod_name,
        #             "namespace": namespace
        #         },
        #         "spec": {
        #             "containers": [
        #                 {
        #                     "name": "terminal",
        #                     "image": "ubuntu",
        #                     "resources": {
        #                         "limits": {
        #                             "cpu": "200m",
        #                             "memory": "128Mi"
        #                         }
        #                     }
        #                 }
        #             ]
        #         }
        #     }
        #     logger.info("Pod manifest prepared:", pod_manifest)

        #     v1.create_namespaced_pod(namespace=namespace, body=pod_manifest)
        #     logger.info("Pod created successfully in Kubernetes:", pod_name)

        #     StudentPod.objects.create(student=request.user, course=course, pod_name=pod_name)
        #     logger.info("Pod information saved in database:", pod_name)

        # except client.exceptions.ApiException as e:
        #     logger.info("Kubernetes API exception occurred:", str(e))
        #     return JsonResponse({"error": f"Failed to create Pod: {e}"}, status=500)

        # 성공 응답(수업 id,name도 반환)
        return JsonResponse({
            "message": "Course registered successfully",
            "course_id": course.id,
            "course_name": course.name
        }, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request format"}, status=400)
    
    except Exception as e:
        logger.error("Unexpected error occurred during course registration:", str(e))
        return JsonResponse({"error": f"Failed to register for course: {e}"}, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def enter_course(request, course_id):
    try:
        user = request.user
        course = Course.objects.get(id=course_id)
        if user.user_type == 't' and course.teacher != user:
            return JsonResponse({"error": "Unauthorized access"}, status=403)
        if user.user_type == 's' and user not in course.participants.all():
            return JsonResponse({"error": "You are not registered for this course"}, status=403)

        return JsonResponse({
            "course_name": course.name,
            "user_name": user.first_name,
            "course_code" : course.code,
        }, status=200)

    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Internal server error", "details": str(e)}, status=500)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def leave_course(request, course_id):
    try:
        return JsonResponse({"message": f"Successfully left the class. course_id : {course_id}"}, status=200)

    except Exception as e:
        return JsonResponse({"error": "Internal server error", "details": str(e)}, status=500)


@csrf_exempt
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def drop_course(request, course_id):
    try:
        if request.user.user_type != 's':
            return JsonResponse({"error": "Only students can drop courses"}, status=403)

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return JsonResponse({"error": "Course not found"}, status=404)

        if not course.participants.filter(id=request.user.id).exists():
            return JsonResponse({"error": "You are not registered for this course"}, status=403)

        try:
            pod_name = f"{course.name.lower()}-{request.user.id}"
            namespace = f"course-{course.id}"
            config.load_incluster_config()
            v1 = client.CoreV1Api()
            v1.delete_namespaced_pod(name=pod_name, namespace=namespace)

            StudentPod.objects.filter(student=request.user, course=course).delete()
        except client.exceptions.ApiException as e:
            return JsonResponse({"error": f"Failed to delete Pod: {e}"}, status=500)

        course.participants.remove(request.user)

        return JsonResponse({"message": "Successfully dropped the course"}, status=200)

    except Exception as e:
        return JsonResponse({"error": "Internal server error", "details": str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_course_progress(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
        
        if request.user != course.teacher:
            return JsonResponse({"error": "Unauthorized access"}, status=403)
            
        participants_data = [{
            'name': student.first_name,
            'id': student.user_id,
            'progress': 0  # 추후 실제 진행률 로직 추가
        } for student in course.participants.all()]
        
        response_data = {
            'course_name': course.name,
            'user_name': request.user.first_name,
            'participants': participants_data
        }
        print(response_data)
        
        return JsonResponse(response_data, status=200)
        
    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found"}, status=404)