from __future__ import annotations

from pathlib import Path

import pytest

from app.knowledge import KnowledgeBase

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "knowledge_sample"


@pytest.fixture
def kb() -> KnowledgeBase:
    kb = KnowledgeBase(str(FIXTURE_PATH))
    kb.load()
    return kb


class TestKnowledgeLoader:
    def test_load_all_files(self, kb: KnowledgeBase):
        docs = kb.get_all()
        assert len(docs) == 9

    def test_load_specific_file(self, kb: KnowledgeBase):
        doc = kb.get("training-philosophy.md")
        assert doc is not None
        assert doc.title == "Running Philosophy"
        assert "80/20" in doc.content

    def test_load_nested_file(self, kb: KnowledgeBase):
        doc = kb.get("workouts/easy-run.md")
        assert doc is not None
        assert doc.title == "Easy Run"

    def test_load_nonexistent_file(self, kb: KnowledgeBase):
        doc = kb.get("nonexistent.md")
        assert doc is None

    def test_file_count_matches(self, kb: KnowledgeBase):
        files = kb.list_files()
        assert len(files) == 9

    def test_reload_works(self, kb: KnowledgeBase):
        kb.reload()
        files = kb.list_files()
        assert len(files) == 9

    def test_title_extracted_from_h1(self, kb: KnowledgeBase):
        doc = kb.get("admin-guidelines.md")
        assert doc is not None
        assert doc.title == "Admin Guidelines"

    def test_tags_inferred_from_path(self, kb: KnowledgeBase):
        doc = kb.get("workouts/easy-run.md")
        assert doc is not None
        assert "Workouts" in doc.tags

    def test_tags_for_nested_path(self, kb: KnowledgeBase):
        doc = kb.get("programs/couch-to-5k.md")
        assert doc is not None
        assert "Programs" in doc.tags


class TestKnowledgeSearch:
    def test_search_by_title(self, kb: KnowledgeBase):
        results = kb.search("Easy Run")
        assert len(results) >= 1
        assert results[0].title == "Easy Run"

    def test_search_by_content(self, kb: KnowledgeBase):
        results = kb.search("Zone 2")
        assert len(results) >= 1

    def test_search_by_tag(self, kb: KnowledgeBase):
        results = kb.search("Workouts")
        assert len(results) >= 1

    def test_search_no_results(self, kb: KnowledgeBase):
        results = kb.search("zzzznotfound")
        assert results == []

    def test_search_max_results(self, kb: KnowledgeBase):
        results = kb.search("run", max_results=2)
        assert len(results) <= 2

    def test_search_returns_relevant_first(self, kb: KnowledgeBase):
        results = kb.search("5k")
        assert len(results) >= 2
        assert results[0].title == "5K Improver" or results[1].title == "5K Improver"

    def test_search_is_case_insensitive(self, kb: KnowledgeBase):
        r1 = kb.search("tempo")
        r2 = kb.search("TEMPO")
        assert len(r1) == len(r2)
        assert r1[0].path == r2[0].path

    def test_get_by_path_prefix(self, kb: KnowledgeBase):
        docs = kb.get_by_path_prefix("workouts")
        assert len(docs) == 2

    def test_get_by_path_prefix_nested(self, kb: KnowledgeBase):
        docs = kb.get_by_path_prefix("programs")
        assert len(docs) == 2


class TestKnowledgeCRUD:
    def test_create_file(self, kb: KnowledgeBase):
        kb.create("test-new.md", "# Test Doc\nTest content.")
        doc = kb.get("test-new.md")
        assert doc is not None
        assert doc.title == "Test Doc"
        kb.delete("test-new.md")

    def test_update_file(self, kb: KnowledgeBase):
        kb.create("test-update.md", "# Original\nOriginal content.")
        kb.update("test-update.md", "# Updated\nUpdated content.")
        doc = kb.get("test-update.md")
        assert doc is not None
        assert "Updated" in doc.content
        kb.delete("test-update.md")

    def test_update_nonexistent_returns_none(self, kb: KnowledgeBase):
        result = kb.update("nonexistent-update.md", "content")
        assert result is None

    def test_delete_file(self, kb: KnowledgeBase):
        kb.create("test-delete.md", "# Delete Me\nContent.")
        assert kb.get("test-delete.md") is not None
        result = kb.delete("test-delete.md")
        assert result is True
        assert kb.get("test-delete.md") is None

    def test_delete_nonexistent(self, kb: KnowledgeBase):
        result = kb.delete("nonexistent.md")
        assert result is False

    def test_get_content(self, kb: KnowledgeBase):
        content = kb.get_content("training-philosophy.md")
        assert content is not None
        assert "80/20" in content

    def test_get_content_nonexistent(self, kb: KnowledgeBase):
        content = kb.get_content("nonexistent.md")
        assert content is None
