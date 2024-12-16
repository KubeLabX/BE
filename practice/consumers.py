import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from kubernetes.stream import stream
from kubernetes import client, config
from practice.models import StudentPod
from asgiref.sync import sync_to_async

class PodTerminalConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope["user"].is_authenticated or self.scope["user"].user_type != "s":
            await self.close(code=401)
            return

        self.course_id = self.scope["url_route"]["kwargs"]["course_id"]
        self.user = self.scope["user"]

        try:
            self.pod_info = await sync_to_async(StudentPod.objects.get)(student=self.user, course_id=self.course_id)
        except StudentPod.DoesNotExist:
            await self.close(code=404)
            return

        # WebSocket 연결 수락
        await self.accept()

        # Pod에 대한 Kubernetes exec 스트림 연결
        config.load_kube_config()
        self.k8s_client = client.CoreV1Api()
        self.k8s_stream = stream(
            self.k8s_client.connect_get_namespaced_pod_exec,
            name=self.pod_info.pod_name,
            namespace=f"course-{self.course_id}",
            command=["/bin/bash"],
            stderr=True,
            stdin=True,
            stdout=True,
            tty=True,
            _preload_content=False
        )

        # Pod에서 데이터를 읽는 asyncio 태스크 실행
        asyncio.create_task(self.read_from_pod())

    async def disconnect(self, close_code):
        # WebSocket 연결 해제 시 Kubernetes 스트림 종료
        if hasattr(self, "k8s_stream") and self.k8s_stream:
            self.k8s_stream.close()

    async def receive(self, text_data):
        # WebSocket으로부터 명령어를 받아 Pod에 전송
        if hasattr(self, "k8s_stream") and self.k8s_stream:
            self.k8s_stream.write_stdin(text_data)

    async def read_from_pod(self):
        # Pod에서 데이터를 읽고 WebSocket으로 전송
        try:
            while True:
                output = self.k8s_stream.read_stdout(timeout=1)
                if output:
                    await self.send(text_data=output)
        except Exception as e:
            await self.send(text_data=f"Error: {str(e)}")
            await self.close()
