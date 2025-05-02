import typing

import fastapi
import itsdangerous

from recordlinker.config import settings


def save_cookie(response: fastapi.Response, key: str, data: dict, **kwargs: typing.Any) -> None:
    """
    Save the session data to the session store.
    """
    serializer = itsdangerous.URLSafeSerializer(settings.secret_key)
    response.set_cookie(
        key,
        value=serializer.dumps(data),
        domain=settings.session_cookie_domain,
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )


def load_cookie(request: fastapi.Request, key: str) -> typing.Optional[dict]:
    """
    Load the session data from the session store.
    """
    value = request.cookies.get(key, None)
    if value is None:
        return None

    serializer = itsdangerous.URLSafeSerializer(settings.secret_key)
    return serializer.loads(value)


def delete_cookie(response: fastapi.Response, key: str) -> None:
    """
    Delete the session data from the session store.
    """
    response.delete_cookie(
        key,
        domain=settings.session_cookie_domain,
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )


def reset_cookie(response: fastapi.Response, key: str) -> None:
    """
    Reset the session data in the session store.
    """
    save_cookie(response, key, {})
