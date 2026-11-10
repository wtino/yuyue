#!/usr/bin/env python3
"""把 ntfy 上的加密反馈解密，并在本仓库里每条开一个 Issue。

ntfy.sh 只缓存大约 12 小时，所以这个脚本要在那之前跑（工作流默认每小时一次）。
解不开、格式不对的消息直接跳过。已经开过的 Issue（正文里有 ntfy-id）不会再开。

环境变量：
  NTFY_TOPIC            话题名
  FEEDBACK_PRIVATE_KEY  keygen.py 打出的私钥（标准 base64，32 字节）
  GH_TOKEN              能在本仓库开 Issue 的 token，Actions 里用 GITHUB_TOKEN
  GH_REPO               owner/name，Actions 里用 github.repository
  NTFY_SERVER           默认 https://ntfy.sh
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

from nacl.public import PrivateKey, SealedBox

ID_RE = re.compile(r"ntfy-id:\s*([^\s<]+)")
CATEGORIES = {"bug": "问题", "idea": "建议", "other": "其他"}


def load_secret(text: str) -> PrivateKey:
    raw = base64.b64decode(re.sub(r"\s+", "", text), validate=True)
    if len(raw) != 32:
        raise ValueError("private key must be 32 bytes")
    return PrivateKey(raw)


def open_message(secret: PrivateKey, message: str) -> dict | None:
    """Return the feedback JSON, or None when the message is junk."""
    text = (message or "").strip()
    if not text.startswith("v1."):
        return None
    try:
        plain = SealedBox(secret).decrypt(base64.b64decode(text[3:], validate=True))
        data = json.loads(plain)
    except Exception:
        return None
    if not isinstance(data, dict) or data.get("v") != 1:
        return None
    body = data.get("text")
    if not isinstance(body, str) or not body.strip():
        return None
    if data.get("category") not in CATEGORIES:
        data["category"] = "other"
    return data


def issue_title(data: dict) -> str:
    label = CATEGORIES.get(data.get("category"), "其他")
    text = " ".join(str(data.get("text", "")).split())
    snippet = text[:40] + ("…" if len(text) > 40 else "")
    return f"[{label}] {snippet}"


def safe_id(ntfy_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "", ntfy_id)[:80]


def issue_body(ntfy_id: str, data: dict) -> str:
    ntfy_id = safe_id(ntfy_id)
    label = CATEGORIES.get(data.get("category"), "其他")
    contact = str(data.get("contact") or "").strip() or "未留"
    when = _when(data.get("sentAt"))
    return (
        f"<!-- ntfy-id: {ntfy_id} -->\n\n"
        f"**类别**：{label}\n"
        f"**平台**：{data.get('platform') or ''}\n"
        f"**系统**：{data.get('os') or ''}\n"
        f"**版本**：{data.get('app') or ''}\n"
        f"**联系**：{contact}\n"
        f"**时间**：{when}\n\n"
        f"{str(data.get('text') or '').strip()}\n"
    )


def known_ids(issues: list) -> set[str]:
    found = set()
    for issue in issues:
        if not isinstance(issue, dict) or "pull_request" in issue:
            continue
        match = ID_RE.search(issue.get("body") or "")
        if match:
            found.add(match.group(1))
    return found


def _when(sent_at) -> str:
    if not isinstance(sent_at, (int, float)):
        return ""
    import time

    return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(sent_at / 1000))


def poll(server: str, topic: str) -> list[dict]:
    query = urllib.parse.urlencode({"poll": "1", "since": "12h"})
    url = f"{server.rstrip('/')}/{urllib.parse.quote(topic, safe='')}/json?{query}"
    req = urllib.request.Request(url, headers={"Accept": "application/x-ndjson"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8", "replace")
    messages = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict) and item.get("event") == "message":
            messages.append(item)
    return messages


def github(method: str, path: str, token: str, body: dict | None = None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        "https://api.github.com" + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "yuyue-feedback",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")
        return err.code, detail


def list_issues(repo: str, token: str) -> list:
    found = []
    for page in range(1, 21):
        status, data = github("GET", f"/repos/{repo}/issues?state=all&per_page=100&page={page}", token)
        if status != 200 or not isinstance(data, list):
            raise SystemExit(f"读 Issue 失败：HTTP {status}")
        found.extend(data)
        if len(data) < 100:
            break
    return found


def main() -> int:
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    secret_text = os.environ.get("FEEDBACK_PRIVATE_KEY", "").strip()
    token = os.environ.get("GH_TOKEN", "").strip()
    repo = os.environ.get("GH_REPO", "").strip()
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh").strip()
    if not topic or not secret_text or not token or not repo:
        print("缺少 NTFY_TOPIC、FEEDBACK_PRIVATE_KEY、GH_TOKEN 或 GH_REPO", file=sys.stderr)
        return 1
    try:
        secret = load_secret(secret_text)
    except Exception:
        print("FEEDBACK_PRIVATE_KEY 不是 32 字节的 base64", file=sys.stderr)
        return 1

    try:
        messages = poll(server, topic)
    except Exception as err:
        print(f"拉取 ntfy 失败：{err}", file=sys.stderr)
        return 1

    issues = list_issues(repo, token)
    seen = known_ids(issues)
    opened = skipped = junk = failed = 0
    for item in messages:
        ntfy_id = safe_id(str(item.get("id") or ""))
        if not ntfy_id or ntfy_id in seen:
            skipped += 1
            continue
        data = open_message(secret, str(item.get("message") or ""))
        if data is None:
            junk += 1
            print(f"跳过解不开的消息 {ntfy_id}")
            continue
        status, detail = github(
            "POST",
            f"/repos/{repo}/issues",
            token,
            {"title": issue_title(data), "body": issue_body(ntfy_id, data)},
        )
        if status not in (200, 201):
            failed += 1
            print(f"开 Issue 失败 {ntfy_id}：HTTP {status} {detail}", file=sys.stderr)
            continue
        seen.add(ntfy_id)
        opened += 1
        print(f"已开 Issue：{issue_title(data)}")

    print(f"完成：新开 {opened}，已有 {skipped}，跳过 {junk}，失败 {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
