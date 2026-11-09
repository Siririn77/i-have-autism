"""A minimal Anthropic Messages endpoint, used to see the prompt Harness actually sends.

Every request body is appended to a JSONL file; the response is a fixed one-word
message, streamed as Server-Sent Events when the request asks for a stream. The
point is the request, not the answer.

    python3 mock_anthropic.py /tmp/dsh_requests.jsonl
    DEEPSEEK_BASE_URL=http://127.0.0.1:8899 dsh --profile headless "say ok"
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/dsh_requests.jsonl"


def events(model: str) -> list[str]:
    """The four SSE frames the client needs to accept one assistant message."""
    return [
        "event: message_start\ndata: " + json.dumps({
            "type": "message_start",
            "message": {"id": "msg_mock", "type": "message", "role": "assistant", "model": model,
                        "content": [], "stop_reason": None, "stop_sequence": None,
                        "usage": {"input_tokens": 1, "output_tokens": 0}},
        }),
        "event: content_block_start\ndata: " + json.dumps(
            {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}),
        "event: content_block_delta\ndata: " + json.dumps(
            {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "ok"}}),
        "event: content_block_stop\ndata: " + json.dumps({"type": "content_block_stop", "index": 0}),
        "event: message_delta\ndata: " + json.dumps(
            {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None},
             "usage": {"output_tokens": 1}}),
        "event: message_stop\ndata: " + json.dumps({"type": "message_stop"}),
    ]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"data": [{"id": "deepseek-v4.1-flash", "type": "model"}]}).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("content-length") or 0)
        raw = self.rfile.read(length)
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"raw": raw.decode("utf-8", "replace")}
        with open(OUT, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"path": self.path, "body": parsed}, ensure_ascii=False) + "\n")

        model = parsed.get("model", "deepseek-v4.1-flash")
        if not parsed.get("stream"):
            body = json.dumps({
                "id": "msg_mock", "type": "message", "role": "assistant", "model": model,
                "content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn",
                "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1},
            }).encode()
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.send_header("cache-control", "no-cache")
        self.end_headers()
        for frame in events(model):
            self.wfile.write((frame + "\n\n").encode())
            self.wfile.flush()

    def log_message(self, *args):
        pass


HTTPServer(("127.0.0.1", 8899), Handler).serve_forever()
