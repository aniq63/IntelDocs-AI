import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# We need to patch heavy imports (database engine, embedding model warm-up)
# BEFORE importing main.py, so the TestClient can be created without a
# real database or embedding model.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_db_and_embeddings(monkeypatch):
    """Patch database engine creation, session factory, and embedding warm-up
    so the FastAPI app can start without a real Postgres or HuggingFace model."""

    # Patch database connection module
    mock_engine = MagicMock()
    mock_session_factory = MagicMock()
    monkeypatch.setattr("database.connection.engine", mock_engine)
    monkeypatch.setattr("database.connection.AsyncSessionLocal", mock_session_factory)

    # Patch embedding warm-up in the lifespan
    monkeypatch.setattr(
        "services.rag.rag_models.warm_up_embeddings_model", lambda: None
    )

    # Patch get_settings to return test values
    mock_settings = MagicMock()
    mock_settings.database_url = "postgresql+asyncpg://test:test@localhost/test"
    mock_settings.debug = False
    mock_settings.session_token_expire_hours = 168
    monkeypatch.setattr("utils.settings.get_settings", lambda: mock_settings)
    monkeypatch.setattr("database.connection.get_settings", lambda: mock_settings)
    monkeypatch.setattr("utils.authentication.get_settings", lambda: mock_settings)

    yield


@pytest.fixture
def client():
    # Import AFTER patches are in place
    from main import app
    return TestClient(app, raise_server_exceptions=False)


class TestRootEndpoint:

    def test_root_returns_message(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "IntelDocs AI" in data["message"]


class TestCompanyRegistration:

    def test_register_missing_fields(self, client):
        resp = client.post(
            "/Company-Authentication/register/company",
            json={},
        )
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        resp = client.post(
            "/Company-Authentication/register/company",
            json={"name": "Test", "email": "bad", "password": "123456"},
        )
        assert resp.status_code == 422


class TestCompanyLogin:

    def test_login_missing_fields(self, client):
        resp = client.post(
            "/Company-Authentication/company/login",
            json={},
        )
        assert resp.status_code == 422

    def test_login_empty_body(self, client):
        resp = client.post(
            "/Company-Authentication/company/login",
            json={"name": "", "password": ""},
        )
        # Empty strings pass Pydantic validation; mocked DB may return 500
        assert resp.status_code in (401, 422, 500)


class TestTeamRegistration:

    def test_team_create_missing_auth(self, client):
        resp = client.post(
            "/Team-Registration/team/create",
            json={"name": "Dev", "password": "secret123"},
        )
        # No session token -> 401 or 422
        assert resp.status_code in (401, 422)


class TestTeamLogin:

    def test_team_login_missing_fields(self, client):
        resp = client.post(
            "/Team-Authentication/team/login",
            json={},
        )
        # Requires company auth header; may return 401 or 422
        assert resp.status_code in (401, 422)


class TestChatRoutes:

    def test_company_ask_no_auth(self, client):
        resp = client.post(
            "/chat/company/ask",
            json={"question": "Hello"},
        )
        assert resp.status_code in (401, 422)

    def test_team_ask_no_auth(self, client):
        resp = client.post(
            "/chat/team/ask",
            json={"question": "Hello"},
        )
        assert resp.status_code in (401, 422)

    def test_company_sessions_no_auth(self, client):
        resp = client.get("/chat/company/sessions")
        assert resp.status_code in (401, 422)

    def test_team_sessions_no_auth(self, client):
        resp = client.get("/chat/team/sessions")
        assert resp.status_code in (401, 422)


class TestKnowledgeRoutes:

    def test_company_upload_no_auth(self, client):
        resp = client.post("/knowledge/company/knowledge/upload")
        assert resp.status_code in (401, 422)

    def test_company_list_no_auth(self, client):
        resp = client.get("/knowledge/company/knowledge")
        assert resp.status_code in (401, 422)

    def test_team_upload_no_auth(self, client):
        resp = client.post("/knowledge/team/knowledge/upload")
        assert resp.status_code in (401, 422)


class TestDashboardRoutes:

    def test_company_overview_no_auth(self, client):
        resp = client.get("/dashboard/company/overview")
        assert resp.status_code in (401, 422)

    def test_team_overview_no_auth(self, client):
        resp = client.get("/dashboard/team/overview")
        assert resp.status_code in (401, 422)

    def test_company_documents_no_auth(self, client):
        resp = client.get("/dashboard/company/documents")
        assert resp.status_code in (401, 422)

    def test_team_documents_no_auth(self, client):
        resp = client.get("/dashboard/team/documents")
        assert resp.status_code in (401, 422)

    def test_company_teams_no_auth(self, client):
        resp = client.get("/dashboard/company/teams")
        assert resp.status_code in (401, 422)


class TestOpenAPI:

    def test_docs_endpoint(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_openapi_json(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        assert "openapi" in data
        assert "paths" in data
