#!/usr/bin/env python3
"""A scripted stand-in for the Anthropic Messages API, to drive a real Claude Code.

Point Claude Code at it with ANTHROPIC_BASE_URL=http://127.0.0.1:PORT and any
ANTHROPIC_API_KEY. Each request that carries tools is answered by the first
rule in the script whose ``when`` substring appears in the last user turn
(text and tool results). Requests without tools (titles, summaries) get "ok".
Every request is logged to the log file as one JSON line, so a test can see
exactly what the harness fed the model, such as a hook's block reason.

usage: fake_anthropic.py SCRIPT.json LOG.jsonl [--port 8765]
"""

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

COUNTER = {"n": 0}


def last_user_text(messages):
    """Flatten the last user message, including tool results, to text."""
    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        content = message.get("content")
        if isinstance(content, str):
            return content
        parts = []
        for block in content:
            if block.get("type") == "text":
                parts.append(block["text"])
            elif block.get("type") == "tool_result":
                inner = block.get("content")
                parts.append(inner if isinstance(inner, str) else json.dumps(inner))
        return "\n".join(parts)
    return ""


def choose(rules, request):
    """Return the reply dict for a request."""
    if not request.get("tools"):
        return {"text": "ok"}
    text = last_user_text(request.get("messages", []))
    for rule in rules:
        if rule["when"] in text:
            return rule["reply"]
    return {"text": "No scripted reply matched; ending."}


def blocks_for(reply):
    """Return content blocks and the stop reason for a reply."""
    COUNTER["n"] += 1
    if "tool" in reply:
        return [{"type": "tool_use", "id": f"toolu_{COUNTER['n']:04d}", "name": reply["tool"], "input": reply["input"]}], "tool_use"
    return [{"type": "text", "text": reply["text"]}], "end_turn"


def sse(handler, event, data):
    """Write one server-sent event."""
    handler.wfile.write(f"event: {event}\ndata: {json.dumps(data)}\n\n".encode())


class Handler(BaseHTTPRequestHandler):
    """Serve /v1/messages, streaming or not."""

    def log_message(self, *args):
        return

    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        request = json.loads(self.rfile.read(length) or b"{}")
        if not self.path.startswith("/v1/messages") or self.path.startswith("/v1/messages/count_tokens"):
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"input_tokens": 10}).encode())
            return
        reply = choose(self.server.rules, request)
        content, stop = blocks_for(reply)
        with open(self.server.log, "a") as fh:
            fh.write(json.dumps({"tools": bool(request.get("tools")), "last_user": last_user_text(request.get("messages", []))[-1500:], "reply": reply}) + "\n")
        message = {"id": f"msg_{COUNTER['n']:04d}", "type": "message", "role": "assistant", "model": request.get("model", "fake"),
                   "content": content, "stop_reason": stop, "stop_sequence": None,
                   "usage": {"input_tokens": 10, "output_tokens": 10}}
        if not request.get("stream"):
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(message).encode())
            return
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.end_headers()
        sse(self, "message_start", {"type": "message_start", "message": {**message, "content": [], "stop_reason": None}})
        for i, block in enumerate(content):
            if block["type"] == "text":
                sse(self, "content_block_start", {"type": "content_block_start", "index": i, "content_block": {"type": "text", "text": ""}})
                sse(self, "content_block_delta", {"type": "content_block_delta", "index": i, "delta": {"type": "text_delta", "text": block["text"]}})
            else:
                sse(self, "content_block_start", {"type": "content_block_start", "index": i, "content_block": {**block, "input": {}}})
                sse(self, "content_block_delta", {"type": "content_block_delta", "index": i, "delta": {"type": "input_json_delta", "partial_json": json.dumps(block["input"])}})
            sse(self, "content_block_stop", {"type": "content_block_stop", "index": i})
        sse(self, "message_delta", {"type": "message_delta", "delta": {"stop_reason": stop, "stop_sequence": None}, "usage": {"output_tokens": 10}})
        sse(self, "message_stop", {"type": "message_stop"})


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("script")
    parser.add_argument("log")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.rules = json.load(open(args.script))
    server.log = args.log
    print(f"fake anthropic on 127.0.0.1:{args.port}", file=sys.stderr, flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
