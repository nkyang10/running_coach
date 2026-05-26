"""GitHub issue/PR helpers for development workflow.

Usage:
  python scripts/dev_workflow.py issue <title> <body>     # Create issue
  python scripts/dev_workflow.py branch <issue-number>     # Create branch
  python scripts/dev_workflow.py commit <message>          # Commit with convention
"""

import subprocess
import sys
from typing import Optional

GITHUB_REPO = "nkyang10/running_coach"


def run(cmd: list[str]) -> tuple[str, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()


def create_issue(title: str, body: str, token: Optional[str] = None) -> None:
    token = token or _get_token()
    if not token:
        print("❌ No GitHub token found. Set GITHUB_TOKEN env var.")
        return
    import httpx

    resp = httpx.post(
        f"https://api.github.com/repos/{GITHUB_REPO}/issues",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"title": title, "body": body},
    )
    if resp.status_code == 201:
        data = resp.json()
        print(f"✅ Issue #{data['number']}: {data['html_url']}")
    else:
        print(f"❌ Failed: {resp.status_code} {resp.text}")


def create_branch(issue_number: str, branch_type: str = "feature") -> None:
    stdout, _ = run(["git", "branch", "--show-current"])
    current = stdout.strip()
    if current != "main" and current != "develop":
        print(
            f"⚠️  Currently on '{current}'. Consider switching to main/develop first."
        )

    branch_name = f"{branch_type}/{issue_number}-work"
    run(["git", "checkout", "-b", branch_name])
    print(f"✅ Created and switched to branch: {branch_name}")


def commit_with_convention(message: str, issue: Optional[str] = None) -> None:
    prefix = ""
    if message.startswith("feat:"):
        prefix = "feat"
    elif message.startswith("fix:"):
        prefix = "fix"
    elif message.startswith("test:"):
        prefix = "test"
    elif message.startswith("docs:"):
        prefix = "docs"
    elif message.startswith("chore:"):
        prefix = "chore"
    elif message.startswith("kb:"):
        prefix = "kb"
    else:
        prefix = message.split(":")[0] if ":" in message else "chore"

    scope = ""
    if "(" in message and ")" in message:
        scope = message[message.index("(") + 1 : message.index(")")]
        msg_clean = message[message.index(")") + 2 :]
    else:
        msg_clean = message

    commit_msg = f"{prefix}"
    if scope:
        commit_msg += f"({scope})"
    commit_msg += f": {msg_clean}"
    if issue:
        commit_msg += f" #{issue}"

    stdout, stderr = run(["git", "commit", "-am", commit_msg])
    print(stdout)
    if stderr:
        print(stderr)
    print(f"✅ Committed: {commit_msg}")


def _get_token() -> Optional[str]:
    import os

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    try:
        stdout, _ = run(["git", "config", "--get", "credential.helper"])
        if stdout:
            return None
    except Exception:
        pass
    return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "issue" and len(sys.argv) >= 4:
        create_issue(sys.argv[2], " ".join(sys.argv[3:]))
    elif cmd == "branch" and len(sys.argv) >= 3:
        create_branch(sys.argv[2])
    elif cmd == "commit" and len(sys.argv) >= 3:
        issue = sys.argv[3] if len(sys.argv) >= 4 else None
        commit_with_convention(sys.argv[2], issue)
    else:
        print(__doc__)
