import pytest
from pydantic import ValidationError
from datetime import datetime

from database.schemas import (
    CompanyCreate,
    CompanyResponse,
    CompanyLogin,
    TokenResponse,
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamLogin,
    DocumentOut,
    ChatAskRequest,
    ChatAskResponse,
    ChatSessionOut,
    ChatMessageOut,
    CompanyOverviewOut,
    TeamOverviewOut,
    TeamSummaryOut,
)


# =============================================================================
# CompanyCreate
# =============================================================================

class TestCompanyCreate:

    def test_valid_company_create(self):
        c = CompanyCreate(name="Acme", email="acme@example.com", password="secret123")
        assert c.name == "Acme"
        assert c.email == "acme@example.com"
        assert c.password == "secret123"

    def test_minimal_name(self):
        c = CompanyCreate(name="A", email="a@b.com", password="123456")
        assert c.name == "A"

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            CompanyCreate(name="x" * 101, email="a@b.com", password="123456")

    def test_name_empty_rejected(self):
        with pytest.raises(ValidationError):
            CompanyCreate(name="", email="a@b.com", password="123456")

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            CompanyCreate(name="Acme", email="a@b.com", password="123")

    def test_passwordexactly_min_length(self):
        c = CompanyCreate(name="Acme", email="a@b.com", password="123456")
        assert c.password == "123456"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            CompanyCreate(name="Acme", email="not-an-email", password="123456")


# =============================================================================
# CompanyLogin
# =============================================================================

class TestCompanyLogin:

    def test_valid_login(self):
        login = CompanyLogin(name="Acme", password="pass123")
        assert login.name == "Acme"

    def test_empty_name_allowed(self):
        login = CompanyLogin(name="", password="pass")
        assert login.name == ""


# =============================================================================
# TokenResponse
# =============================================================================

class TestTokenResponse:

    def test_valid_token(self):
        t = TokenResponse(access_token="abc123", token_type="simple")
        assert t.access_token == "abc123"


# =============================================================================
# TeamCreate / TeamUpdate / TeamResponse
# =============================================================================

class TestTeamCreate:

    def test_valid_team(self):
        t = TeamCreate(name="Dev", description="Dev team", password="secret123")
        assert t.name == "Dev"
        assert t.description == "Dev team"

    def test_no_description(self):
        t = TeamCreate(name="Dev", password="secret123")
        assert t.description is None

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            TeamCreate(name="x" * 101, password="123456")

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            TeamCreate(name="Dev", password="12")


class TestTeamUpdate:

    def test_all_optional(self):
        u = TeamUpdate()
        assert u.name is None
        assert u.description is None
        assert u.password is None

    def test_partial_update(self):
        u = TeamUpdate(name="NewName")
        assert u.name == "NewName"
        assert u.description is None

    def test_name_too_long_rejected(self):
        with pytest.raises(ValidationError):
            TeamUpdate(name="x" * 101)

    def test_password_too_short_rejected(self):
        with pytest.raises(ValidationError):
            TeamUpdate(password="12")


class TestTeamLogin:

    def test_valid_team_login(self):
        tl = TeamLogin(company_name="Acme", team_name="Dev", password="pass123")
        assert tl.company_name == "Acme"


# =============================================================================
# DocumentOut
# =============================================================================

class TestDocumentOut:

    def test_valid_document_out(self):
        d = DocumentOut(
            id=1, company_id=1, team_id=None,
            doc_length=10, source="test.pdf",
            visibility="company", status="ready",
            uploaded_at=datetime(2024, 1, 1),
        )
        assert d.source == "test.pdf"
        assert d.team_id is None


# =============================================================================
# Chat schemas
# =============================================================================

class TestChatAskRequest:

    def test_valid_request(self):
        r = ChatAskRequest(question="What is AI?")
        assert r.session_id is None

    def test_with_session(self):
        r = ChatAskRequest(question="Hello", session_id=42)
        assert r.session_id == 42


class TestChatAskResponse:

    def test_valid_response(self):
        r = ChatAskResponse(
            session_id=1, message_id=2,
            question="Hi", answer="Hello!"
        )
        assert r.answer == "Hello!"


class TestChatSessionOut:

    def test_valid_session_out(self):
        s = ChatSessionOut(
            id=1, title="Chat 1", visibility="company",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 2),
        )
        assert s.title == "Chat 1"


class TestChatMessageOut:

    def test_valid_message(self):
        m = ChatMessageOut(
            id=1, question="Q", answer="A",
            created_at=datetime(2024, 1, 1),
        )
        assert m.question == "Q"


# =============================================================================
# Dashboard schemas
# =============================================================================

class TestCompanyOverviewOut:

    def test_valid_overview(self):
        o = CompanyOverviewOut(total_documents=5, total_teams=3)
        assert o.total_documents == 5
        assert o.total_teams == 3


class TestTeamOverviewOut:

    def test_valid_overview(self):
        o = TeamOverviewOut(total_documents=10)
        assert o.total_documents == 10


class TestTeamSummaryOut:

    def test_valid_summary(self):
        s = TeamSummaryOut(
            id=1, name="Dev", description="Team",
            created_at=datetime(2024, 1, 1),
        )
        assert s.name == "Dev"
