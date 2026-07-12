import importlib.util
import json
import os
import tempfile
import threading
import unittest
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("routeiq_v171", ROOT / "agent.py")
AGENT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(AGENT)


class _Handler(BaseHTTPRequestHandler):
    calls = 0

    def log_message(self, format, *args):
        return

    def do_POST(self):
        type(self).calls += 1
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if "response_format" in payload:
            body = json.dumps({"error": "unsupported in mock"}).encode("utf-8")
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        content = json.dumps({"r": [{"i": 0, "a": "Tokyo"}]})
        body = json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class RuntimeSafetyTests(unittest.TestCase):
    def test_extracts_list_content(self):
        body = {"choices": [{"message": {"content": [{"text": "{\"r\":[]}"}]}}]}
        self.assertEqual(AGENT.extract_message_content(body), '{"r":[]}')

    def test_structured_rejection_falls_back_to_plain_json(self):
        _Handler.calls = 0
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            AGENT.ACTIVE_DEADLINE = AGENT.time.monotonic() + 10
            result = AGENT.request_batch(
                [{"task_id": "f", "task_type": "factual knowledge", "prompt": "Capital of Japan?"}],
                "minimax-m3",
                "mock",
                f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
            )
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(result, {"f": "Tokyo"})
        self.assertEqual(_Handler.calls, 2)

    def test_remote_failure_is_not_reported_as_container_crash(self):
        tasks = [{"task_id": "f", "task_type": "factual knowledge", "prompt": "Capital of Japan?"}]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            AGENT.INPUT_PATH = root / "tasks.json"
            AGENT.OUTPUT_PATH = root / "results.json"
            AGENT.INPUT_PATH.write_text(json.dumps(tasks), encoding="utf-8")
            previous = {key: os.environ.get(key) for key in ("ALLOWED_MODELS", "FIREWORKS_BASE_URL", "FIREWORKS_API_KEY")}
            os.environ["ALLOWED_MODELS"] = '["minimax-m3"]'
            os.environ["FIREWORKS_BASE_URL"] = "http://127.0.0.1:1/v1"
            os.environ["FIREWORKS_API_KEY"] = "x"
            old_timeout = AGENT.REQUEST_TIMEOUT_SECONDS
            old_deadline = AGENT.GLOBAL_DEADLINE_SECONDS
            AGENT.REQUEST_TIMEOUT_SECONDS = 0.25
            AGENT.GLOBAL_DEADLINE_SECONDS = 2
            try:
                status = AGENT.main()
            finally:
                AGENT.REQUEST_TIMEOUT_SECONDS = old_timeout
                AGENT.GLOBAL_DEADLINE_SECONDS = old_deadline
                for key, value in previous.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
            self.assertEqual(status, 0)
            self.assertEqual(json.loads(AGENT.OUTPUT_PATH.read_text()), [{"task_id": "f", "answer": ""}])


if __name__ == "__main__":
    unittest.main()
