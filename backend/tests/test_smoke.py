from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_health(): assert client.get('/health').json()=={'status':'ok'}
def test_catalog_needs_no_auth(): assert client.get('/categories').status_code==200
