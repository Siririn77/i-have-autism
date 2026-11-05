#!/usr/bin/env python3
"""Create the GitHub release for a tag that is already pushed.

Usage: python3 tools/create_release.py v0.4.0 notes.md
Reads the token from $GITHUB_TOKEN or /tmp/gh_token. The token needs
Contents: Read and write on this repository; a read-only token returns 403.
"""
import json
import os
import sys
import urllib.error
import urllib.request

REPO = "Siririn77/i-have-autism"
DOC = "usage: create_release.py <tag> <notes.md>"


def main() -> int:
    if len(sys.argv) != 3:
        print(DOC)
        return 2
    tag, notes_path = sys.argv[1], sys.argv[2]
    token = os.environ.get("GITHUB_TOKEN") or open("/tmp/gh_token").read().strip()
    body = open(notes_path, encoding="utf-8").read()
    first_line = body.splitlines()[0].lstrip("# ").strip()

    payload = {
        "tag_name": tag,
        "name": first_line,
        "body": body,
        "draft": False,
        "prerelease": False,
        "make_latest": "true",
    }
    request = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/releases",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        print(f"HTTP {error.code}: {error.read().decode()[:400]}")
        if error.code == 403:
            print("The token is read-only. Enable Contents: Read and write for this repository.")
        return 1
    print(f"{response.status} {data['tag_name']} {data['html_url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
