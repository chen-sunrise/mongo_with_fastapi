from datetime import datetime, timedelta, timezone

import jwt

from app.core import security, settings


def test_password_hash_and_verify_roundtrip():
    plain_password = "correct-horse-battery-staple"

    hashed_password = security.get_password_hash(plain_password)

    assert hashed_password != plain_password
    assert security.verify_password(plain_password, hashed_password)
    assert security.verify_password("another-password", hashed_password) is False


def test_create_access_token_casts_subject_to_string():
    token = security.create_access_token(subject=12345)

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])

    assert payload["sub"] == "12345"


def test_create_access_token_honors_custom_expiration():
    expires_delta = timedelta(minutes=5)
    before_create = datetime.now(timezone.utc)

    token = security.create_access_token(subject="user-1", expires_delta=expires_delta)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])

    exp_value = payload["exp"]
    if isinstance(exp_value, datetime):
        exp_time = exp_value.astimezone(timezone.utc)
    else:
        exp_time = datetime.fromtimestamp(exp_value, tz=timezone.utc)

    after_create = datetime.now(timezone.utc)
    tolerance = timedelta(seconds=3)

    assert before_create + expires_delta - tolerance <= exp_time
    assert exp_time <= after_create + expires_delta + tolerance
