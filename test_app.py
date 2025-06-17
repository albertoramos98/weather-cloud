import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "testsecret"
    with app.test_client() as client:
        yield client

def test_login_get(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert "Senha" in response.get_data(as_text=True)

def test_login_success(client):
    response = client.post('/login', data={'senha': 'admin'}, follow_redirects=True)
    assert response.status_code == 200
    assert "Logout" in response.get_data(as_text=True) or "index" in response.get_data(as_text=True)

def test_login_fail(client):
    response = client.post('/login', data={'senha': 'senhaerrada'}, follow_redirects=True)
    assert response.status_code == 200
    assert "Senha incorreta" in response.get_data(as_text=True)

def test_logout(client):
    # Faz login
    client.post('/login', data={'senha': 'admin'}, follow_redirects=True)
    
    # Faz logout
    response = client.get('/logout', follow_redirects=True)
    text = response.get_data(as_text=True)
    assert "Você saiu da sessão" in text
