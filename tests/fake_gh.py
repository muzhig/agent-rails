#!/usr/bin/env python3
"""A fake ``gh`` that serves the subset ghflow, checklist and workers use.

State lives in the JSON file named by FAKE_GH_STATE (calls are serialised
with a lock file). Every call is appended to ``state["calls"]`` so tests can
assert what was (not) written. Setting ``state["drop"]`` to a list such as
``["comments"]`` makes those POSTs answer 201 without persisting: the write
that looks done but isn't. ``state["pr_feedback"][PR]`` holds a PR's
``comments``, ``review_comments`` and ``reviews``.
"""

import fcntl
import json
import os
import re
import sys
from urllib.parse import parse_qs, unquote, urlparse


def load():
    """Load the fake's state."""
    return json.loads(open(os.environ["FAKE_GH_STATE"]).read())


def save(state):
    """Persist the fake's state."""
    open(os.environ["FAKE_GH_STATE"], "w").write(json.dumps(state, indent=2))


def fail(code, msg):
    """Exit like gh does on an HTTP error."""
    print(f"gh: {msg} (HTTP {code})", file=sys.stderr)
    sys.exit(1)


def issue_view(issue):
    """Render an issue the way the REST API does."""
    return {
        "number": issue["number"], "title": issue.get("title", ""), "state": issue.get("state", "open"),
        "labels": [{"name": n} for n in issue.get("labels", [])],
        "assignees": [{"login": a} for a in issue.get("assignees", [])],
        "comments": len(issue.get("comments", [])),
    }


def flag(args, name):
    """Return the value after ``name`` in args, or None."""
    return args[args.index(name) + 1] if name in args else None


def porcelain(args, state):
    """Serve the two porcelain commands workers use: issue view and pr create."""
    if args[:2] == ["issue", "view"]:
        issue = state["issues"].get(args[2]) or fail(404, "Not Found")
        print(f"#{issue['number']} {issue.get('title', '')}\nlabels: {', '.join(issue.get('labels', []))}\n\n{issue.get('body', '')}")
        for comment in issue.get("comments", []) if "--comments" in args else []:
            print(f"\n--- {comment['user']['login']}:\n{comment['body']}")
        return
    if args[:2] == ["pr", "create"]:
        body_file = flag(args, "--body-file")
        body = open(body_file).read() if body_file else flag(args, "--body") or ""
        number = 100 + len(state.setdefault("pulls", []))
        url = f"https://github.com/o/r/pull/{number}"
        state["pulls"].append({"number": number, "title": flag(args, "--title"), "body": body, "state": "open",
                               "merged_at": None, "html_url": url, "head": {"ref": flag(args, "--head")}})
        print(url)
        return
    save(state)
    fail(400, f"fake gh does not support: {' '.join(args[:2])}")


def api(args, state):
    """Serve ``gh api -X METHOD PATH [--paginate] [--input -]``."""
    method, path, body = "GET", None, None
    rest, i = args[1:], 0
    while i < len(rest):
        if rest[i] == "-X":
            method = rest[i + 1]
            i += 2
        elif rest[i] == "--input":
            body = json.loads(sys.stdin.read() or "null")
            i += 2
        elif rest[i] == "--paginate":
            i += 1
        else:
            path = rest[i]
            i += 1
    url = urlparse(path)
    query = parse_qs(url.query)
    route = re.sub(r"^repos/[^/]+/[^/]+/", "", url.path)
    issues = state.setdefault("issues", {})
    if route == "user":
        return {"login": state["me"]}
    if route == "labels" and method == "GET":
        return [{"name": n} for n in state.setdefault("repo_labels", [])]
    if route == "labels" and method == "POST":
        if body["name"] in state.setdefault("repo_labels", []):
            save(state)
            fail(422, "Validation Failed")
        state["repo_labels"].append(body["name"])
        return {"name": body["name"]}
    if route == "issues" and method == "GET":
        wanted = query.get("labels", [None])[0]
        out = [issue_view(x) for x in issues.values() if not wanted or wanted in x.get("labels", [])]
        return out + [{"number": p["number"], "pull_request": {}, "state": p["state"], "labels": []} for p in state.get("pulls", [])]
    if route == "pulls":
        return state.get("pulls", [])
    m = re.fullmatch(r"(?:pulls/(\d+)/(comments|reviews)|issues/(\d+)/comments)", route)
    pr_numbers = {str(p["number"]) for p in state.get("pulls", [])}
    if m and (m.group(1) or m.group(3) in pr_numbers):
        number = m.group(1) or m.group(3)
        kind = {"comments": "review_comments", "reviews": "reviews"}[m.group(2)] if m.group(1) else "comments"
        return state.get("pr_feedback", {}).get(number, {}).get(kind, [])
    m = re.fullmatch(r"issues/(\d+)(?:/(assignees|labels|comments)(?:/(.+))?)?", route)
    if not m:
        save(state)
        fail(404, f"fake gh has no route for {method} {route}")
    issue = issues.get(m.group(1))
    if issue is None:
        save(state)
        fail(404, "Not Found")
    sub, name = m.group(2), m.group(3)
    if sub is None:
        return issue_view(issue)
    if sub == "assignees":
        if method == "POST":
            issue["assignees"] = sorted(set(issue.get("assignees", [])) | set(body["assignees"]))
        else:
            issue["assignees"] = [a for a in issue.get("assignees", []) if a not in body["assignees"]]
        return issue_view(issue)
    if sub == "labels" and name:
        name = unquote(name)
        if name not in issue.get("labels", []):
            save(state)
            fail(404, "Label does not exist")
        issue["labels"].remove(name)
        return [{"name": n} for n in issue["labels"]]
    if sub == "labels":
        if "labels" not in state.get("drop", []):
            issue["labels"] = sorted(set(issue.get("labels", [])) | set(body["labels"]))
        return [{"name": n} for n in issue["labels"]]
    if method == "POST":
        state["next_id"] = state.get("next_id", 1000) + 1
        comment = {"id": state["next_id"], "body": body["body"], "user": {"login": state["me"]},
                   "html_url": f"https://github.com/o/r/issues/{issue['number']}#issuecomment-{state['next_id']}"}
        if "comments" not in state.get("drop", []):
            issue.setdefault("comments", []).append(comment)
        return comment
    return issue.get("comments", [])


def main():
    """Dispatch one gh invocation against the state file."""
    args = sys.argv[1:]
    state = load()
    state.setdefault("calls", []).append(args)
    if args[:1] != ["api"]:
        porcelain(args, state)
        save(state)
        return
    out = api(args, state)
    save(state)
    print(json.dumps(out))


if __name__ == "__main__":
    with open(os.environ["FAKE_GH_STATE"] + ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        main()
