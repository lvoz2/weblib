import functools
import secrets
from typing import Any, Callable, Optional

import flask


def use_csrf(func: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        csrf_token: Optional[str] = flask.session.get("csrf_token", None)
        if csrf_token is None:
            return {"status": False, "error": "Bad CSRF token"}
        data: Optional[dict[str, Any]] = flask.request.json
        if data is None:
            return {"status": False, "error": "Bad CSRF token"}
        given_token: str = (
            (data["csrf_token"] if isinstance(data["csrf_token"], str) else "")
            if "csrf_token" in data
            else ""
        )
        if given_token == "" or given_token != csrf_token:
            return {"status": False, "error": "Bad CSRF token"}
        return func(*args, **kwargs)

    return wrapper


def get_csrf_token() -> str:
    token: Optional[str] = flask.session.get("csrf_token", None)
    if token is None:
        csrf_token: str = secrets.token_urlsafe()
        flask.session["csrf_token"] = csrf_token
        return csrf_token
    return token
