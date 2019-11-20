from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async
from django.http.request import QueryDict


from threading import Thread
import paramiko
import socket
import base64
import json


class SSH:
    def __init__(self, websocket, message):
        self.websocket = websocket
        self.message = message
        self.channel = None

    def connect(self, host, user, password=None, port=22,
                timeout=30, term='xterm', width=80, height=24):
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(username=user, password=password, hostname=host, port=port, timeout=timeout)

            transport = ssh_client.get_transport()
            self.channel = transport.open_session()
            self.channel.get_pty(term=term, width=width, height=height)
            self.channel.invoke_shell()
            recv = self.channel.recv(102400).decode('utf-8')
            self.message['status'] = 0
            self.message['message'] = recv
            message = json.dumps(self.message)
            self.websocket.send(message)
        except socket.timeout:
            self.message['status'] = 1
            self.message['message'] = 'ssh 连接超时'
            message = json.dumps(self.message)
            self.websocket.send(message)
            self.close()
        except (Exception,):
            self.close()

    def resize_pty(self, cols, rows):
        self.channel.resize_pty(width=cols, height=rows)

    def django_to_ssh(self, data):
        try:
            self.channel.send(data)
        except (Exception,):
            self.close()

    def websocket_to_django(self):
        try:
            while True:
                data = self.channel.recv(1024).decode('utf-8')
                if not len(data):
                    return
                self.message['status'] = 0
                self.message['message'] = data
                message = json.dumps(self.message)
                self.websocket.send(message)
        except (Exception,):
            self.close()

    def close(self):
        self.message['status'] = 1
        self.message['message'] = '关闭连接'
        message = json.dumps(self.message)
        self.websocket.send(message)
        self.channel.close()
        self.websocket.close()

    def shell(self, data):
        Thread(target=self.django_to_ssh, args=(data,)).start()
        Thread(target=self.websocket_to_django).start()


class SSHConsumer(WebsocketConsumer):
    message = {'status': 0, 'message': None}
    """
     status:
         0: ssh 连接正常, websocket 正常
         1: 发生未知错误, 关闭 ssh 和 websocket 连接
     message:
         status 为 1 时, message 为具体的错误信息
         status 为 0 时, message 为 ssh 返回的数据, 前端页面将获取 ssh 返回的数据并写入终端页面
     """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ssh = None

    def connect(self):
        self.accept()
        query_string = self.scope.get('query_string')
        ssh_args = QueryDict(query_string=query_string, encoding='utf-8')

        width = int(ssh_args.get('width'))
        height = int(ssh_args.get('height'))
        port = int(ssh_args.get('port'))
        user = ssh_args.get('user')
        host = ssh_args.get('host')
        password = ssh_args.get('password')
        if password:
            password = base64.b64decode(password).decode('utf-8')
        self.ssh = SSH(websocket=self, message=self.message)
        self.ssh.connect(
            host=host, port=port, user=user, password=password,
            width=width, height=height
        )

    def disconnect(self, code):
        self.ssh.close()

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        if isinstance(data, dict):
            status = data['status']
            if status == 0:
                data = data['data']
                self.ssh.shell(data)
            else:
                cols = data['cols']
                rows = data['rows']
                self.ssh.resize_pty(cols=cols, rows=rows)
