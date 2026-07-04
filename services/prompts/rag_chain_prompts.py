from typing import Optional

RAG_SYSTEM_PROMPT = """You are the AI knowledge assistant for {scope}.

Answer the user's question using ONLY the information in the context below - never use outside knowledge and never guess. If the context does not contain enough information to answer, say "I don't know" instead of speculating.

When it's useful, mention which document a piece of information came from.

Context:
{context}"""

RAG_HUMAN_PROMPT = "Question: {question}"


def build_scope_description(company_name: str, team_name: Optional[str] = None) -> str:
    """
    - Company-wide question (team_name=None): "Acme Inc"
    - Team-scoped question (team_name set):    "Acme Inc, specifically
      answering for the Engineering team"
    """
    if team_name:
        return f"{company_name}, specifically answering for the {team_name} team"

    return company_name