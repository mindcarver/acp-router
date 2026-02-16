"""ACP (Agent Client Protocol) JSON-RPC 传输层

实现 ACP 协议的 JSON-RPC 2.0 通信，用于与支持 ACP 的 Agent 交互。
"""

from __future__ import annotations

import json
import subprocess
import threading
import queue
import time
from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class ACPMessage:
    """ACP 消息"""
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    method: Optional[str] = None
    params: Optional[dict] = None
    result: Optional[Any] = None
    error: Optional[dict] = None

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        data = {"jsonrpc": self.jsonrpc}
        if self.id is not None:
            data["id"] = self.id
        if self.method is not None:
            data["method"] = self.method
        if self.params is not None:
            data["params"] = self.params
        return json.dumps(data)


class ACPTransport:
    """ACP JSON-RPC 传输层

    管理 ACP Agent 子进程，通过 stdin/stdout 进行 JSON-RPC 通信。
    """

    def __init__(
        self,
        command: str,
        args: list[str],
        protocol_version: str = "2024-11-05",
        client_info: dict | None = None,
        timeout: int = 120,
    ):
        """
        初始化 ACP 传输层

        Args:
            command: 启动 Agent 的命令
            args: 命令参数
            protocol_version: ACP 协议版本
            client_info: 客户端信息
            timeout: 请求超时时间（秒）
        """
        self.command = command
        self.args = args
        self.protocol_version = protocol_version
        self.client_info = client_info or {"name": "acp-router", "version": "0.1.0"}
        self.timeout = timeout

        self.process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._response_queue: queue.Queue = queue.Queue()
        self._notification_queue: queue.Queue = queue.Queue()
        self._running = False
        self._stdout_thread: Optional[threading.Thread] = None
        self._stderr_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """启动 ACP Agent 子进程"""
        if self.process is not None:
            return

        cmd = [self.command] + self.args
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # 行缓冲
        )

        self._running = True

        # 启动读取线程
        self._stdout_thread = threading.Thread(
            target=self._read_stdout,
            daemon=True,
        )
        self._stdout_thread.start()

        self._stderr_thread = threading.Thread(
            target=self._read_stderr,
            daemon=True,
        )
        self._stderr_thread.start()

        # ACP 握手
        self._initialize()

    def stop(self) -> None:
        """停止 ACP Agent 子进程"""
        if not self._running:
            return

        self._running = False

        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            finally:
                self.process = None

    def _read_stdout(self) -> None:
        """读取 Agent 的 stdout 输出"""
        if not self.process or not self.process.stdout:
            return

        for line in iter(self.process.stdout.readline, ""):
            if not line:
                break
            line = line.strip()
            if line:
                try:
                    message = json.loads(line)
                    if message.get("jsonrpc") == "2.0":
                        if "id" in message:
                            self._response_queue.put(message)
                        else:
                            self._notification_queue.put(message)
                except json.JSONDecodeError:
                    pass  # 忽略非 JSON 行

    def _read_stderr(self) -> None:
        """读取 Agent 的 stderr 日志"""
        if not self.process or not self.process.stderr:
            return

        for line in iter(self.process.stderr.readline, ""):
            if not line:
                break
            # 可以记录日志
            pass

    def _initialize(self) -> None:
        """执行 ACP 握手

        1. 发送 initialize 请求
        2. 发送 initialized 通知
        """
        try:
            # 发送 initialize (protocolVersion 是整数)
            self.send_request(
                "initialize",
                {
                    "protocolVersion": 1,  # 整数版本
                    "capabilities": {},
                    "clientInfo": self.client_info,
                },
            )
            # 发送 initialized 通知
            self.send_notification("initialized")
        except Exception as e:
            raise RuntimeError(f"ACP 握手失败: {e}")

    def send_request(
        self,
        method: str,
        params: dict | None = None,
        collect_notifications: bool = False,
    ) -> Any:
        """
        发送 JSON-RPC 请求并等待响应

        Args:
            method: 方法名
            params: 参数
            collect_notifications: 是否收集 session/update 通知

        Returns:
            响应结果，如果 collect_notifications=True 则返回 (result, notifications)

        Raises:
            RuntimeError: 请求失败或超时
        """
        if not self.process or not self.process.stdin:
            raise RuntimeError("ACP Agent 未运行")

        self._request_id += 1
        request = ACPMessage(
            id=self._request_id,
            method=method,
            params=params,
        )

        # 清空通知队列
        while not self._notification_queue.empty():
            try:
                self._notification_queue.get_nowait()
            except queue.Empty:
                break

        # 发送请求
        message = request.to_json() + "\n"
        self.process.stdin.write(message)
        self.process.stdin.flush()

        # 收集通知（如果需要）
        notifications = []
        response = None  # 初始化变量

        # 等待响应
        start_time = time.time()
        while True:
            if time.time() - start_time > self.timeout:
                raise RuntimeError(f"ACP 请求超时 ({self.timeout}s)")

            # 检查是否有通知
            if collect_notifications:
                try:
                    while not self._notification_queue.empty():
                        notification = self._notification_queue.get_nowait()
                        notifications.append(notification)
                except queue.Empty:
                    pass

            try:
                response = self._response_queue.get(timeout=0.1)
                if response.get("id") == self._request_id:
                    if "error" in response:
                        raise RuntimeError(f"ACP 错误: {response['error']}")
                    if collect_notifications:
                        return response.get("result"), notifications
                    return response.get("result")
                # 不是我们的响应，放回队列
                self._response_queue.put(response)
            except queue.Empty:
                # 检查是否已经收到最终响应（通过 stopReason）
                if collect_notifications and notifications:
                    last_notification = notifications[-1] if notifications else {}
                    # 检查是否是包含 stopReason 的响应
                    if isinstance(last_notification, dict):
                        params = last_notification.get("params", {})
                        update = params.get("update", {})
                        if update.get("stopReason"):
                            # 收到 stopReason，返回空结果和收集的通知
                            return {}, notifications
                # 没有响应，继续等待
                response = None
                continue

    def send_notification(
        self,
        method: str,
        params: dict | None = None,
    ) -> None:
        """
        发送 JSON-RPC 通知（无响应）

        Args:
            method: 方法名
            params: 参数
        """
        if not self.process or not self.process.stdin:
            raise RuntimeError("ACP Agent 未运行")

        notification = ACPMessage(
            method=method,
            params=params,
        )

        message = notification.to_json() + "\n"
        self.process.stdin.write(message)
        self.process.stdin.flush()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
