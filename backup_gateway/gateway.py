"""
备用网关 - 轻量级 HTTP 代理转发
"""
import http.server
import socketserver
import urllib.request
import urllib.error
import sys
import os
import logging
import threading
import time
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from socketserver import ThreadingMixIn

from .config import settings

logger = logging.getLogger(__name__)


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    timeout = 30

    def do_GET(self):
        self.proxy_request()

    def do_POST(self):
        self.proxy_request()

    def do_PUT(self):
        self.proxy_request()

    def do_DELETE(self):
        self.proxy_request()

    def do_PATCH(self):
        self.proxy_request()

    def do_HEAD(self):
        self.proxy_request()

    def do_OPTIONS(self):
        self.proxy_request()

    def proxy_request(self):
        start_time = time.time()
        backend_url = settings.BACKEND_URL
        url = backend_url + self.path

        try:
            method = self.command
            headers = dict(self.headers)

            body = None
            if "Content-Length" in headers:
                length = int(headers["Content-Length"])
                body = self.rfile.read(length)

            req = urllib.request.Request(url, data=body, method=method)

            for header, value in headers.items():
                if header.lower() not in ["host", "content-length"]:
                    req.add_header(header, value)

            req.add_header("X-Forwarded-For", self.client_address[0])
            req.add_header("X-Forwarded-Proto", "http")

            with urllib.request.urlopen(req, timeout=settings.CHECK_TIMEOUT) as response:
                response_body = response.read()
                self.send_response(response.getcode())

                for header, value in response.getheaders():
                    if header.lower() not in ["transfer-encoding", "connection"]:
                        self.send_header(header, value)

                self.send_header("Content-Length", len(response_body))
                self.send_header("X-Served-By", "backup-gateway")
                self.end_headers()
                self.wfile.write(response_body)

            duration = time.time() - start_time
            logger.debug(f"{method} {self.path} -> {response.getcode()} ({duration:.3f}s)")

        except urllib.error.HTTPError as e:
            self.send_error_response(e.code, str(e.reason))
        except urllib.error.URLError as e:
            self.send_error_response(502, f"Bad Gateway: {e.reason}")
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            self.send_error_response(502, f"Bad Gateway: {str(e)}")

    def send_error_response(self, code: int, message: str):
        try:
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-Served-By", "backup-gateway")
            self.end_headers()
            error_body = {
                "error": message,
                "code": code,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self.wfile.write(str(error_body).encode())
        except Exception:
            pass

    def log_message(self, format, *args):
        logger.info("%s - %s", self.client_address[0], format % args)


class ThreadedTCPServer(ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


class BackupGateway:
    def __init__(self, port: Optional[int] = None, backend_url: Optional[str] = None):
        self.port = port or settings.PORT
        self.backend_url = backend_url or settings.BACKEND_URL
        self._server: Optional[ThreadedTCPServer] = None
        self._running = False
        self._start_time: Optional[datetime] = None
        self._request_count = 0
        self._error_count = 0

    def start(self):
        if self._running:
            logger.warning("Gateway is already running")
            return

        try:
            self._server = ThreadedTCPServer(("", self.port), ProxyHandler)
            self._running = True
            self._start_time = datetime.now(timezone.utc)

            logger.info(
                f"Backup gateway started on port {self.port}, "
                f"forwarding to {self.backend_url}"
            )

            self._server.serve_forever()
        except OSError as e:
            logger.error(f"Failed to start gateway: {e}")
            raise
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        if not self._running:
            return

        logger.info("Stopping backup gateway...")
        self._running = False

        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None

        logger.info("Backup gateway stopped")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "port": self.port,
            "backend_url": self.backend_url,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "uptime_seconds": (
                (datetime.now(timezone.utc) - self._start_time).total_seconds()
                if self._start_time
                else 0
            ),
            "request_count": self._request_count,
            "error_count": self._error_count,
        }

    def is_healthy(self) -> bool:
        return self._running


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    gateway = BackupGateway()

    try:
        gateway.start()
    except KeyboardInterrupt:
        gateway.stop()
    except Exception as e:
        logger.error(f"Gateway error: {e}")
        gateway.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
