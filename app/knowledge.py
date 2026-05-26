from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.logger import get_logger

logger = get_logger(__name__)


class KnowledgeDoc:
    def __init__(
        self, path: str, title: str, content: str, tags: list[str] | None = None
    ) -> None:
        self.path = path
        self.title = title
        self.content = content
        self.tags = tags or []


class KnowledgeBase:
    def __init__(self, kb_path: str | Path) -> None:
        self.kb_path = Path(kb_path)
        self._docs: dict[str, KnowledgeDoc] = {}
        self._loaded = False

    def load(self) -> None:
        self._docs = {}
        if not self.kb_path.exists():
            logger.warning("knowledge_path_not_found", path=str(self.kb_path))
            self._loaded = True
            return

        md_files = sorted(self.kb_path.rglob("*.md"))
        for md_file in md_files:
            rel_path = str(md_file.relative_to(self.kb_path)).replace("\\", "/")
            content = md_file.read_text(encoding="utf-8")
            title = self._extract_title(content, rel_path)
            tags = self._infer_tags(rel_path)
            doc = KnowledgeDoc(path=rel_path, title=title, content=content, tags=tags)
            self._docs[rel_path] = doc

        self._loaded = True
        logger.info("knowledge_loaded", count=len(self._docs), path=str(self.kb_path))

    def reload(self) -> None:
        self.load()

    def get_all(self) -> list[KnowledgeDoc]:
        return list(self._docs.values())

    def get(self, path: str) -> Optional[KnowledgeDoc]:
        return self._docs.get(path)

    def get_by_path_prefix(self, prefix: str) -> list[KnowledgeDoc]:
        return [doc for path, doc in self._docs.items() if path.startswith(prefix)]

    def search(self, query: str, max_results: int = 5) -> list[KnowledgeDoc]:
        query_lower = query.lower()
        scored: list[tuple[KnowledgeDoc, int]] = []

        for doc in self._docs.values():
            score = 0
            content_lower = doc.content.lower()

            if query_lower in doc.title.lower():
                score += 10
            if query_lower in doc.path.lower():
                score += 8
            for tag in doc.tags:
                if query_lower in tag.lower():
                    score += 6

            count = content_lower.count(query_lower)
            score += count

            if score > 0:
                scored.append((doc, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored[:max_results]]

    def list_files(self) -> list[str]:
        return sorted(self._docs.keys())

    def create(self, path: str, content: str) -> KnowledgeDoc:
        full_path = self.kb_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        title = self._extract_title(content, path)
        tags = self._infer_tags(path)
        doc = KnowledgeDoc(path=path, title=title, content=content, tags=tags)
        self._docs[path] = doc
        logger.info("knowledge_created", path=path)
        return doc

    def update(self, path: str, content: str) -> Optional[KnowledgeDoc]:
        full_path = self.kb_path / path
        if not full_path.exists():
            return None
        full_path.write_text(content, encoding="utf-8")
        title = self._extract_title(content, path)
        tags = self._infer_tags(path)
        doc = KnowledgeDoc(path=path, title=title, content=content, tags=tags)
        self._docs[path] = doc
        logger.info("knowledge_updated", path=path)
        return doc

    def delete(self, path: str) -> bool:
        full_path = self.kb_path / path
        if not full_path.exists():
            return False
        full_path.unlink()
        self._docs.pop(path, None)
        logger.info("knowledge_deleted", path=path)
        return True

    def get_content(self, path: str) -> Optional[str]:
        doc = self._docs.get(path)
        return doc.content if doc else None

    @staticmethod
    def _extract_title(content: str, path: str) -> str:
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("##"):
                return stripped[2:].strip()
        stem = path.replace("\\", "/").split("/")[-1]
        if stem.endswith(".md"):
            stem = stem[:-3]
        return stem.replace("-", " ").title()

    @staticmethod
    def _infer_tags(path: str) -> list[str]:
        parts = path.replace("\\", "/").split("/")
        tags = []
        for part in parts[:-1]:
            tags.append(part.replace("_", " ").replace("-", " ").title())
        return tags
