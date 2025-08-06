import base64
import functools
import hashlib
import secrets
from typing import Any, Callable, Literal, Optional, TypeAlias
from urllib import error as url_error
from urllib import parse

import bs4
import flask
import requests


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


SRI_Algorithms: TypeAlias = Literal["sha256"] | Literal["sha384"] | Literal["sha512"]


def use_sri(
    app: flask.Flask,
    hash_alg: SRI_Algorithms = "sha512",
) -> Callable[[Callable[..., str]], Callable[..., str]]:
    def decorator(func: Callable[..., str]) -> Callable[..., str]:
        if hash_alg not in ["sha256", "sha384", "sha512"]:
            raise ValueError(
                "SRI hashes can only be created using sha256, sha384, or sha512. "
                + "See https://developer.mozilla.org/en-US/docs/Web/Security/"
                + "Subresource_Integrity for more info on SRI"
            )

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            html: str = func(*args, **kwargs)
            if app.static_folder is not None:
                soup = bs4.BeautifulSoup(html, "html.parser")
                sri_tags = soup.find_all(
                    ["link", "script"], integrity="<integrity_hash>"
                )
                hashes: dict[str, str] = {}
                for tag in sri_tags:
                    if not isinstance(tag, bs4.Tag):
                        continue
                    src: str | bs4.AttributeValueList = tag[
                        "href" if tag.name == "link" else "src"
                    ]
                    if not isinstance(src, str):
                        continue
                    try:
                        if src in hashes:
                            tag["integrity"] = hashes[src]
                            continue
                        hash: str = create_sri_hash(src, hash_alg)
                        hashes[src] = hash
                        tag["integrity"] = hash
                    except url_error.HTTPError:
                        del tag["integrity"]
                new_html = soup.encode(formatter="html5")
                if isinstance(new_html, bytes):
                    return new_html.decode("utf-8")
                elif isinstance(new_html, str):
                    return new_html
                return str(new_html)
            return html

        return wrapper

    return decorator


def create_sri_hash(
    uri: str,
    hash_alg: SRI_Algorithms = "sha512",
) -> str:
    if hash_alg not in ["sha256", "sha384", "sha512"]:
        raise ValueError(
            "SRI hashes can only be created using sha256, sha384, or sha512. "
            + "See https://developer.mozilla.org/en-US/docs/Web/Security/"
            + "Subresource_Integrity for more info on SRI"
        )
    if parse.urlparse(uri).netloc == "":
        with open(uri[1:], "rb") as f:
            digest: bytes = hashlib.file_digest(f, hash_alg).digest()
    else:
        headers = {"User-Agent": "WebLib/1.0 (https://github.com/lvoz2/weblib)"}
        res = requests.get(uri, headers=headers, timeout=1.0)
        if res.status_code == 408:
            raise url_error.HTTPError(
                uri,
                408,
                "Failed to get resource on the Internet within 1s",
                res.headers,
                None,
            )
        elif res.status_code != 200:
            raise url_error.HTTPError(
                uri,
                res.status_code,
                "Failed to get resource on the Internet",
                res.headers,
                None,
            )
        sha_hash = hashlib.new(hash_alg)
        sha_hash.update(res.text)
        digest = sha_hash.digest()
    b64: bytes = base64.b64encode(digest)
    hash: str = hash_alg + "-" + b64.decode(encoding="ascii")
    return hash


def get_csrf_token() -> str:
    token: Optional[str] = flask.session.get("csrf_token", None)
    if token is None:
        csrf_token: str = secrets.token_urlsafe()
        flask.session["csrf_token"] = csrf_token
        return csrf_token
    else:
        return token
