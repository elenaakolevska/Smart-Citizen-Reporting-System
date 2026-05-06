
from fastapi.testclient import TestClient
from uuid import UUID

from app.main import app
from app.schemas.user import CurrentUser, UserRole
from app.utils.dependencies import get_current_user, require_roles


fake_user = CurrentUser(
    id=UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6"),
    email="user@example.com",
    role=UserRole.citizen
)


def override_get_current_user():
    return fake_user

def override_require_roles(*roles):
    return fake_user


app.dependency_overrides[get_current_user] = override_get_current_user
app.dependency_overrides[require_roles] = override_require_roles

client = TestClient(app)
API_PREFIX = "/api/v1"


def test_list_reports():
    response = client.get(f"{API_PREFIX}/reports")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)