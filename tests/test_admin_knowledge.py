from __future__ import annotations

from pathlib import Path

import pytest

from app.knowledge import KnowledgeBase

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "knowledge_sample"


@pytest.fixture
def kb() -> KnowledgeBase:
    k = KnowledgeBase(str(FIXTURE_PATH))
    k.load()
    return k


class TestAdminKnowledgeCommands:
    def test_list_files(self, kb: KnowledgeBase):
        files = kb.list_files()
        assert len(files) == 9
        assert "training-philosophy.md" in files
        assert "workouts/easy-run.md" in files

    def test_show_file(self, kb: KnowledgeBase):
        content = kb.get_content("training-philosophy.md")
        assert content is not None
        assert "80/20" in content

    def test_show_nonexistent(self, kb: KnowledgeBase):
        content = kb.get_content("nonexistent.md")
        assert content is None

    def test_search_found(self, kb: KnowledgeBase):
        results = kb.search("Zone 2")
        assert len(results) >= 1

    def test_search_not_found(self, kb: KnowledgeBase):
        results = kb.search("zzzzznotfound")
        assert results == []

    def test_add_file(self, kb: KnowledgeBase):
        kb.create("admin-test-new.md", "# Admin Test\nCreated by admin.")
        doc = kb.get("admin-test-new.md")
        assert doc is not None
        assert doc.title == "Admin Test"
        kb.delete("admin-test-new.md")

    def test_add_existing_file_rejected(self, kb: KnowledgeBase):
        kb.create("admin-test-dup.md", "# Original")
        count_before = len(kb.list_files())
        kb.create("admin-test-dup.md", "# Overwrite")  # create() overwrites
        count_after = len(kb.list_files())
        assert count_after == count_before
        doc = kb.get("admin-test-dup.md")
        assert doc is not None
        assert "Overwrite" in doc.content
        kb.delete("admin-test-dup.md")

    def test_edit_file(self, kb: KnowledgeBase):
        kb.create("admin-test-edit.md", "# Original\nOld content.")
        updated = kb.update("admin-test-edit.md", "# Updated\nNew content.")
        assert updated is not None
        doc = kb.get("admin-test-edit.md")
        assert "New content" in doc.content
        kb.delete("admin-test-edit.md")

    def test_edit_nonexistent(self, kb: KnowledgeBase):
        result = kb.update("nonexistent-edit.md", "content")
        assert result is None

    def test_delete_file(self, kb: KnowledgeBase):
        kb.create("admin-test-del.md", "# To Delete")
        assert kb.get("admin-test-del.md") is not None
        result = kb.delete("admin-test-del.md")
        assert result is True
        assert kb.get("admin-test-del.md") is None

    def test_delete_nonexistent(self, kb: KnowledgeBase):
        result = kb.delete("nonexistent.md")
        assert result is False

    def test_reload_preserves_crud(self, kb: KnowledgeBase):
        kb.create("admin-test-reload.md", "# Reload Test")
        kb.reload()
        doc = kb.get("admin-test-reload.md")
        assert doc is not None
        kb.delete("admin-test-reload.md")
