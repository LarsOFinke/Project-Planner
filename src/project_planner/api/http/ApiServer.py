import socket
from threading import Thread
from time import monotonic, sleep

import uvicorn

from project_planner.api.http.app_factory import create_app
from project_planner.shared.settings.Settings import Settings


class ApiServer:
    def __init__(self, settings: Settings, host: str = "127.0.0.1", port: int = 0) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((host, port))
        self._socket.listen(2048)
        actual_port = int(self._socket.getsockname()[1])
        self.base_url = f"http://{host}:{actual_port}/api/v1"
        config = uvicorn.Config(
            create_app(settings, cors_origins=settings.api_cors_origins),
            log_level="warning",
            access_log=False,
        )
        self._server = uvicorn.Server(config)
        self._thread = Thread(
            target=self._server.run,
            kwargs={"sockets": [self._socket]},
            name="project-planner-api",
            daemon=True,
        )

    def start(self, timeout: float = 10.0) -> None:
        self._thread.start()
        deadline = monotonic() + timeout
        while not self._server.started:
            if not self._thread.is_alive():
                self._socket.close()
                raise RuntimeError("The local Project Planner API failed to start")
            if monotonic() >= deadline:
                self._server.should_exit = True
                self._thread.join(1.0)
                raise TimeoutError("Timed out while starting the local Project Planner API")
            sleep(0.01)

    def stop(self, timeout: float = 10.0) -> None:
        self._server.should_exit = True
        self._thread.join(timeout)
        if self._thread.is_alive():
            self._server.force_exit = True
            self._thread.join(1.0)
