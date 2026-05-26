from __future__ import annotations


from app.logger import get_logger

logger = get_logger(__name__)


def format_doc_list(docs: list[str]) -> str:
    if not docs:
        return "No knowledge files found."
    lines = ["📚 Knowledge Base Files:\n"]
    for doc in docs:
        lines.append(f"  📄 {doc}")
    return "\n".join(lines)


def format_doc_content(path: str, content: str) -> str:
    max_len = 3500
    if len(content) > max_len:
        content = content[:max_len] + "\n\n... (truncated)"
    return f"📄 *{path}*\n\n```\n{content}\n```"
