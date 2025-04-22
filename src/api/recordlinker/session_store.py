import typing

import fastapi
import itsdangerous

from recordlinker.config import settings


def save_session(response: fastapi.Response, key: str, data: dict, **kwargs: typing.Any) -> None:
    """
    Save the session data to the session store.
    """
    serializer = itsdangerous.URLSafeSerializer(settings.secret_key)
    response.set_cookie(
        key,
        value=serializer.dumps(data),
        max_age=0,
        domain=settings.session_cookie_domain,
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )


def load_session(request: fastapi.Request, key: str) -> typing.Optional[dict]:
    """
    Load the session data from the session store.
    """
    value = request.cookies.get(key, None)
    if value is None:
        return None

    serializer = itsdangerous.URLSafeSerializer(settings.secret_key)
    return serializer.loads(value)
