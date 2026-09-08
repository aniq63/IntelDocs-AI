import pytest

from services.prompts.rag_chain_prompts import (
    RAG_SYSTEM_PROMPT,
    RAG_HUMAN_PROMPT,
    build_scope_description,
)


class TestBuildScopeDescription:

    def test_company_only(self):
        result = build_scope_description("Acme Inc")
        assert result == "Acme Inc"

    def test_company_and_team(self):
        result = build_scope_description("Acme Inc", team_name="Engineering")
        assert result == "Acme Inc, specifically answering for the Engineering team"

    def test_team_name_none(self):
        result = build_scope_description("Google", team_name=None)
        assert result == "Google"

    def test_empty_company_name(self):
        result = build_scope_description("")
        assert result == ""

    def test_empty_team_name(self):
        result = build_scope_description("Acme", team_name="")
        # empty string is falsy, so team_name=None branch
        assert result == "Acme"


class TestPromptTemplates:

    def test_system_prompt_has_placeholders(self):
        assert "{scope}" in RAG_SYSTEM_PROMPT
        assert "{context}" in RAG_SYSTEM_PROMPT

    def test_human_prompt_has_placeholder(self):
        assert "{question}" in RAG_HUMAN_PROMPT

    def test_system_prompt_mentions_no_outside_knowledge(self):
        assert "never use outside knowledge" in RAG_SYSTEM_PROMPT.lower() or \
               "only the information" in RAG_SYSTEM_PROMPT.lower()
