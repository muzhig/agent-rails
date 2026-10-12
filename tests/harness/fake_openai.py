#!/usr/bin/env python3
"""A scripted stand-in for the OpenAI Responses API, to drive a real Codex CLI.

Configure Codex with a model provider whose base_url is
http://127.0.0.1:PORT/v1 and ``wire_api = "responses"``. Each request is
answered by the first rule whose ``when`` substring appears in the newest
non-assistant input item (user or developer text, or a tool output). A reply
is ``{"text": ...}`` or ``{"shell": "command"}``; the shell call is sent with
the name and argument shape of whichever shell tool the request offers. Each
request is logged as one JSON line with the tool names it offered.

usage: fake_openai.py SCRIPT.json LOG.jsonl [--port 8766]
"""

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

COUNTER = {"n": 0}
SHELL_TOOLS = ("exec_command", "shell_command", "shell", "local_shell")


def newest_input_text(items):
    """Return the text of the newest input item not written by the assistant."""
    for item in reversed(items if isinstance(items, list) else []):
        if item.get("type") == "function_call_output":
            output = item.get("output")
            return output if isinstance(output, str) else json.dumps(output)
        if item.get("type") == "message" and item.get("role") in ("user", "developer"):
            content = item.get("content")
            if isinstance(content, str):
                return content
            return "\n".join(part.get("text", "") for part in content)
    return ""


def tool_names(request):
    """Return the names of the tools offered in the request."""
    return [t.get("name") or t.get("type") for t in request.get("tools", [])]


def shell_call(request, command):
    """Build a function_call item for the request's shell tool."""
    names = tool_names(request)
    name = next((n for n in SHELL_TOOLS if n in names), "shell")
    if name == "exec_command":
        args = {"cmd": command}
    elif name == "shell_command":
        args = {"command": command}
    else:
        args = {"command": ["bash", "-lc", command]}
    COUNTER["n"] += 1
    return {"type": "function_call", "id": f"fc_{COUNTER['n']}", "call_id": f"call_{COUNTER['n']}", "name": name,
            "arguments": json.dumps(args), "status": "completed"}


def choose(rules, request):
    """Return the output item for a request."""
    text = newest_input_text(request.get("input"))
    reply = next((r["reply"] for r in rules if r["when"] in text), {"text": "No scripted reply matched; ending."})
    if "shell" in reply:
        return shell_call(request, reply["shell"]), reply
    COUNTER["n"] += 1
    return {"type": "message", "id": f"msg_{COUNTER['n']}", "role": "assistant", "status": "completed",
            "content": [{"type": "output_text", "text": reply["text"], "annotations": []}]}, reply


def sse(handler, data):
    """Write one server-sent event."""
    handler.wfile.write(f"event: {data['type']}\ndata: {json.dumps(data)}\n\n".encode())


class Handler(BaseHTTPRequestHandler):
    """Serve POST /v1/responses as an event stream; answer GET /v1/models."""

    def log_message(self, *args):
        return

    def do_GET(self):
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"object": "list", "data": [{"id": "fake-model", "object": "model"}], "models": []}).encode())

    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        request = json.loads(self.rfile.read(length) or b"{}")
        item, reply = choose(self.server.rules, request)
        with open(self.server.log, "a") as fh:
            fh.write(json.dumps({"path": self.path, "tools": tool_names(request),
                                 "newest_input": newest_input_text(request.get("input"))[-1500:], "reply": reply}) + "\n")
        rid = f"resp_{COUNTER['n']}"
        usage = {"input_tokens": 10, "input_tokens_details": {"cached_tokens": 0}, "output_tokens": 10,
                 "output_tokens_details": {"reasoning_tokens": 0}, "total_tokens": 20}
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.end_headers()
        sse(self, {"type": "response.created", "response": {"id": rid, "status": "in_progress"}})
        sse(self, {"type": "response.output_item.added", "output_index": 0, "item": item})
        if item["type"] == "message":
            sse(self, {"type": "response.output_text.delta", "item_id": item["id"], "output_index": 0, "content_index": 0,
                       "delta": item["content"][0]["text"]})
        sse(self, {"type": "response.output_item.done", "output_index": 0, "item": item})
        sse(self, {"type": "response.completed", "response": {"id": rid, "status": "completed", "output": [item], "usage": usage}})


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("script")
    parser.add_argument("log")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.rules = json.load(open(args.script))
    server.log = args.log
    print(f"fake responses api on 127.0.0.1:{args.port}", file=sys.stderr, flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
