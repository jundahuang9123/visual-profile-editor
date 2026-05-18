from fastapi.testclient import TestClient

from app.main import app


def test_app_starts_with_construct_dcat_config():
    client = TestClient(app)
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
