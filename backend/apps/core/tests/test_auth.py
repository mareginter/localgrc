def test_login_required_on_home(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login/" in response.url


def test_login_and_home(client, user):
    r = client.post("/login/", {"username": "user@test.local", "password": "pass1234word!"})
    assert r.status_code == 302
    assert client.get("/").status_code == 200


def test_user_create_form_applies_django_password_validators(db):
    from apps.core.forms import UserCreateForm

    weak = UserCreateForm(data={
        "first_name": "New",
        "last_name": "User",
        "email": "new-user@test.local",
        "is_active": True,
        "password": "short",
    })
    assert not weak.is_valid()
    assert "password" in weak.errors

    strong = UserCreateForm(data={
        "first_name": "New",
        "last_name": "User",
        "email": "new-user@test.local",
        "is_active": True,
        "password": "V3ry-Long-Unique!Passphrase",
    })
    assert strong.is_valid(), strong.errors


def test_user_update_form_applies_password_validators(user):
    from apps.core.forms import UserUpdateForm

    form = UserUpdateForm(
        data={
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "is_active": True,
            "new_password": "short",
        },
        instance=user,
    )
    assert not form.is_valid()
    assert "new_password" in form.errors
