#!/usr/bin/env python3
"""把私有仓库里的反馈 Issue 导入本机 Kaneo，一条 Issue 一张任务。

不使用 Kaneo 的 GitHub App，也不需要公网 Webhook。Kaneo 的「Import GitHub issues」
要先装 GitHub App，而 App 的实时同步要求一个公网回调地址，这台 Mac 没有。
这里直接读 GitHub Issue，再调用 Kaneo 的「创建任务」。

幂等：任务描述第一行是 `yuyue-feedback-issue:<编号>`。已经有这行的不再创建。
删掉 Kaneo 里的任务后，下次运行会再导入一次。

配置放在 ~/.config/yuyue/feedback.env（权限 600），也可用同名环境变量盖过文件：

  GITHUB_TOKEN       细粒度 token，只读这个仓库的 Issues
  GITHUB_REPO        默认 wtino/yuyue-feedback
  KANEO_BASE         例如 http://127.0.0.1:8000/api   （浏览器地址后面加 /api）
  KANEO_API_KEY      Kaneo 账户里创建的 API key，需要能读项目、创建任务
  KANEO_PROJECT_ID   项目 ID（打开项目时 URL 里的那一段）
  KANEO_STATUS       可选，列的 slug。不填就用第一列未完成的列

用法：
  python3 kaneo_import.py            # 导入
  python3 kaneo_import.py --dry-run  # 只打印会创建什么
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

MARKER_RE = re.compile(r"yuyue-feedback-issue:(\d+)")
PRIORITY = {"问题": "high", "建议": "medium", "其他": "low"}


def load_env_file() -> None:
    path = os.path.expanduser("~/.config/yuyue/feedback.env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def request(method: str, url: str, token: str, body: dict | None = None, github: bool = False):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json", "User-Agent": "yuyue-feedback"}
    if github:
        headers["Accept"] = "application/vnd.github+json"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")
        if err.code == 429:
            wait = int(err.headers.get("Retry-After") or "2")
            time.sleep(min(wait, 30))
        return err.code, detail


def github_issues(repo: str, token: str) -> list[dict]:
    found = []
    for page in range(1, 21):
        status, data = request(
            "GET",
            f"https://api.github.com/repos/{repo}/issues?state=all&per_page=100&page={page}",
            token,
            github=True,
        )
        if status != 200 or not isinstance(data, list):
            raise SystemExit(f"读 GitHub Issue 失败：HTTP {status}")
        found.extend(item for item in data if "pull_request" not in item)
        if len(data) < 100:
            break
    return found


def column_slug(base: str, project: str, token: str) -> str:
    chosen = os.environ.get("KANEO_STATUS", "").strip()
    if chosen:
        return chosen
    status, data = request("GET", f"{base}/column/{project}", token)
    if status != 200 or not isinstance(data, list) or not data:
        raise SystemExit(f"读 Kaneo 列失败：HTTP {status}。确认 KANEO_BASE 以 /api 结尾，项目 ID 正确。")
    open_columns = [col for col in data if not col.get("isFinal")]
    col = (open_columns or data)[0]
    slug = col.get("slug") or col.get("id")
    if not slug:
        raise SystemExit("Kaneo 没有可用的列")
    return slug


def seen_issue_numbers(base: str, project: str, token: str) -> set[int]:
    seen: set[int] = set()
    page = 1
    while page <= 50:
        status, data = request("GET", f"{base}/task/tasks/{project}?limit=100&page={page}", token)
        if status != 200 or not isinstance(data, dict):
            raise SystemExit(f"读 Kaneo 任务失败：HTTP {status}")
        board = data.get("data") or {}
        buckets = [col.get("tasks") or [] for col in board.get("columns") or []]
        buckets.append(board.get("archivedTasks") or [])
        buckets.append(board.get("plannedTasks") or [])
        for tasks in buckets:
            for task in tasks:
                seen.update(int(n) for n in MARKER_RE.findall(task.get("description") or ""))
        pagination = data.get("pagination") or {}
        total = int(pagination.get("totalPages") or 1)
        if page >= total:
            break
        page += 1
    return seen


def priority_for(body: str) -> str:
    for label, priority in PRIORITY.items():
        if f"**类别**：{label}" in body:
            return priority
    return "low"


def task_description(repo: str, number: int, body: str) -> str:
    text = re.sub(r"<!--.*?-->", "", body or "", flags=re.S).strip()
    return f"yuyue-feedback-issue:{number}\nhttps://github.com/{repo}/issues/{number}\n\n{text}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="把语阅反馈 Issue 导入本机 Kaneo")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不创建任务")
    args = parser.parse_args()
    load_env_file()

    gh_token = os.environ.get("GITHUB_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPO", "wtino/yuyue-feedback").strip()
    base = os.environ.get("KANEO_BASE", "").rstrip("/")
    kaneo = os.environ.get("KANEO_API_KEY", "").strip()
    project = os.environ.get("KANEO_PROJECT_ID", "").strip()
    missing = [
        name
        for name, value in (
            ("GITHUB_TOKEN", gh_token),
            ("KANEO_BASE", base),
            ("KANEO_API_KEY", kaneo),
            ("KANEO_PROJECT_ID", project),
        )
        if not value
    ]
    if missing:
        print("还缺：" + "、".join(missing) + "。写在 ~/.config/yuyue/feedback.env", file=sys.stderr)
        return 2

    issues = [item for item in github_issues(repo, gh_token) if "ntfy-id:" in (item.get("body") or "")]
    seen = seen_issue_numbers(base, project, kaneo)
    status_slug = column_slug(base, project, kaneo)
    created = skipped = 0
    for issue in issues:
        number = int(issue["number"])
        if number in seen:
            skipped += 1
            continue
        title = (issue.get("title") or f"反馈 #{number}")[:200]
        description = task_description(repo, number, issue.get("body") or "")
        priority = priority_for(issue.get("body") or "")
        if args.dry_run:
            print(f"将创建：{title}  →  {status_slug} / {priority}")
            created += 1
            continue
        code, detail = request(
            "POST",
            f"{base}/task/{project}",
            kaneo,
            {"title": title, "description": description, "priority": priority, "status": status_slug},
        )
        if code != 200:
            print(f"创建任务失败 #{number}：HTTP {code} {detail}", file=sys.stderr)
            return 1
        created += 1
        print(f"已导入 #{number} {title}")
    print(f"完成：新建 {created}，已在 Kaneo 里 {skipped}。列：{status_slug}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
