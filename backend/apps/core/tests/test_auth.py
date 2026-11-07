def test_login_required_on_home(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login/" in response.url


def test_login_and_home(client, user):
    r = client.post("/login/", {"username": "user@test.local", "password": "pass1234word!"})
    assert r.status_code == 302
    assert client.get("/").status_code == 200
