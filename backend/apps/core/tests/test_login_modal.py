import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.mark.django_db
def test_login_page_renders_accessible_modal(client):
    response = client.get(reverse("login"), {"next": "/risks/"})
    assert response.status_code == 200
    assert b'role="dialog"' in response.content
    assert b'aria-modal="true"' in response.content
    assert b'name="next" value="/risks/"' in response.content
    assert b'Iniciar sess' in response.content


@pytest.mark.django_db
def test_login_modal_authenticates_and_returns_to_requested_page(client):
    user = get_user_model().objects.create_user(email="login-modal@test.local", password="Strong-Test-Password-2026!")
    response = client.post(reverse("login"), {"username": user.email, "password": "Strong-Test-Password-2026!", "next": "/risks/"})
    assert response.status_code == 302
    assert response["Location"] == "/risks/"
    assert client.session["_auth_user_id"] == str(user.pk)


@pytest.mark.django_db
def test_login_modal_shows_error_for_invalid_credentials(client):
    response = client.post(reverse("login"), {"username": "wrong@test.local", "password": "incorrect"})
    assert response.status_code == 200
    assert b'role="dialog"' in response.content
    assert b'role="alert"' in response.content
    assert b'palavra-passe' in response.content


@pytest.mark.django_db
def test_authenticated_navigation_exposes_post_logout_action(client, user):
    client.force_login(user)
    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert b'Terminar sess' in response.content
    assert b'method="post"' in response.content
    assert b'action="/logout/"' in response.content
    assert b'name="csrfmiddlewaretoken"' in response.content


@pytest.mark.django_db
def test_logout_action_ends_session_and_redirects_to_login(client, user):
    client.force_login(user)

    response = client.post(reverse("logout"))

    assert response.status_code == 302
    assert response["Location"] == "/login/"
    assert "_auth_user_id" not in client.session
    login_response = client.get(reverse("home"))
    assert login_response.status_code == 302
    assert "/login/" in login_response.url
