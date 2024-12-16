import json
from venv import logger
from django.views.decorators.csrf import csrf_exempt
from course.models import Course
from user.models import User
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from kubernetes import client, config
from practice.models import StudentPod


@csrf_exempt
# JWT 토큰 인증 요구
@authentication_classes([JWTAuthentication])
#인증된 사용자만 -> 추후 인증 불필요
@permission_classes([IsAuthenticated])
#POST만 허용(REST API 뷰용)
@api_view(['POST'])
def create_course(request):
    try:
        #교수님인 경우만
        if request.user.user_type != 't':
            return JsonResponse({"error": "Only teachers can create courses"}, status=403)
        
        data = json.loads(request.body)
        #data의 이름 추출
        name = data.get('name')
        
        #이름이 공백인 경우
        if not name or not name.strip():
            return JsonResponse({"error": "Course name is required"}, status=400)
        
        #수업 생성
        course = Course.objects.create(
            name=name.strip(),
            teacher=request.user
        )
        config.load_incluster_config()  # Kubernetes 클러스터 설정 로드
        v1 = client.CoreV1Api()
        namespace_manifest = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": f"course-{course.id}"
            }
        }
        v1.create_namespace(body=namespace_manifest)

        return JsonResponse({
            "message": "Course created successfully",
            "course_id": course.id,
            "course_name": course.name,
            "course_code": course.code
        }, status=201)

    except client.exceptions.ApiException as e:
        # k8s 네임스페이스 생성 실패 시 수업 삭제
        course.delete()
        return JsonResponse({"error": f"Failed to create k8s namespace: {e}"}, status=500)

    # 잘못된 형식
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    # 서버 오류
    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=500)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def list_up_courses(request):
    try:
        #반환을 위한 request 사용자명, 사용자 타입 추출
        user_name = request.user.first_name
        user_role = request.user.user_type

        # 역할에 따라서
        if user_role == 't': #교수인 경우
            courses = Course.objects.filter(teacher=request.user)
            course_data = [{
                'id': c.id,
                'name': c.name,
                'participant_count': c.participants.count(),
                'created_at': c.created_at,
            } for c in courses]

        elif user_role == 's': #학생인 경우
            courses = Course.objects.filter(participants=request.user)
            course_data = [{
                'id': c.id,
                'name': c.name,
                'teacher_name': c.teacher.first_name,
                'created_at': c.created_at,
            } for c in courses]

        else: #그외 처리
            return JsonResponse(
                {"error": "Invalid user role"}, 
                status=400
            )
        
        return JsonResponse({
            "courses": course_data,
            "name": user_name,
            "role": user_role
        }, status=200)

    except Exception as e:
        logger.error(f"Error in list_up_courses: {str(e)}")
        return JsonResponse(
            {"error": str(e)}, 
            status=500
        )


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

    course.delete()
    return JsonResponse({"message": "Course ended successfully"}, status=200)


@csrf_exempt
@api_view(['POST']) 
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def register_course(request):
    try:
        # 교수님은 참여가 불가
        if request.user.user_type == 't':
            return JsonResponse({
                "error": "Teachers cannot register for courses"
            }, status=403)
        
        data = json.loads(request.body)
        #data의 code 데이터 get
        code = data.get('code')

        #코드형태 점검
        if not code:
            return JsonResponse({
                "error": "Course code is required"
            }, status=400)
        
        # 수업 조회
        try:
            course = Course.objects.get(code=code)
        except Course.DoesNotExist:
            return JsonResponse({
                "error": "Invalid course code"
            }, status=404)

        # 중복 참여 확인
        if course.participants.filter(id=request.user.id).exists():
            return JsonResponse({
                "error": "You are already registered for this course"
            }, status=400)
        
        course.participants.add(request.user)

        # Pod 생성 로직
        try:
            pod_name = f"{course.name.lower()}-{request.user.id}"
            namespace = f"course-{course.id}"
            # 이미 Pod 정보가 존재하면 그대로 사용
            if StudentPod.objects.filter(student=request.user, course=course).exists():
                return JsonResponse({"message": "You have already been assigned a Pod.", "pod_name": pod_name},
                                    status=200)
            # Kubernetes Pod 생성
            config.load_incluster_config()
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

        # 성공 응답(수업 id,name도 반환)
        return JsonResponse({
            "message": "Course registered successfully",
            "course_id": course.id,
            "course_name": course.name
        }, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid request format"
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error in register_course: {str(e)}")
        return JsonResponse({
            "error": "Failed to register for course"
        }, status=500)


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
            "course_code" : course.code,  # 현재 로그인한 사용자 이름 추가
        }, status=200)

    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Internal server error", "details": str(e)}, status=500)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_course_progress(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
        
        # 교수자 권한 확인
        if request.user != course.teacher:
            return JsonResponse({"error": "Unauthorized access"}, status=403)
            
        # 학생 목록과 진행률 데이터
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