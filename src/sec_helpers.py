import base64
import functools
import hashlib
import secrets
from urllib import error as url_error, parse
from typing import Callable, Literal, Optional

import bs4
import requests


def use_csrf(session, request):
    def decorator(func: Callable[..., str]):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            user_id: Optional[int] = session.get("user_id", None)
            csrf_token: Optional[str] = session.get("csrf_token", None)
            if csrf_token is None:
                return {"status": False, "error": "Bad CSRF token"}
            data = request.json
            given_token: str = (
                (data["csrf_token"] if isinstance(data["csrf_token"], str) else "")
                if "csrf_token" in data
                else ""
            )
            if given_token == "" or given_token != csrf_token:
                return {"status": False, "error": "Bad CSRF token"}
            return func(*args, **kwargs)

        return wrapper

    return decorator


def use_sri(
    app,
    hash_alg: Literal["sha256"] | Literal["sha384"] | Literal["sha512"] = "sha512",
):
    def decorator(func: Callable[..., str]):
        if hash_alg not in ["sha256", "sha384", "sha512"]:
            raise ValueError(
                "SRI hashes can only be created using sha256, sha384, or sha512. See https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity for more info on SRI"
            )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            html: str = func(*args, **kwargs)
            if app.static_folder is not None:
                soup = bs4.BeautifulSoup(html, "html.parser")
                sri_tags = soup.find_all(
                    ["link", "script"], integrity="<integrity_hash>"
                )
                hashes: dict[str, str] = {}
                for tag in sri_tags:
                    src: str = tag["href" if tag.name == "link" else "src"]
                    try:
                        if src in hashes:
                            tag["integrity"] = hashes[src]
                            continue
                        hash: str = create_sri_hash(src, hash_alg)
                        hashes[src] = hash
                        tag["integrity"] = hash
                    except url_error.HTTPError as e:
                        del tag["integrity"]
                return soup.encode(formatter="html5")
            return html

        return wrapper

    return decorator


def create_sri_hash(
    uri: str,
    hash_alg: Literal["sha256"] | Literal["sha384"] | Literal["sha512"] = "sha512",
) -> str:
    if hash_alg not in ["sha256", "sha384", "sha512"]:
        raise ValueError(
            "SRI hashes can only be created using sha256, sha384, or sha512. See https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity for more info on SRI"
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
                f"Failed to get resource on the Internet within 1s",
                res.headers,
            )
        elif res.status_code != 200:
            raise url_error.HTTPError(
                uri,
                res.status_code,
                f"Failed to get resource on the Internet",
                res.headers,
            )
        digest: bytes = hashlib.new(hash_alg).update(res.text).digest()
    b64: bytes = base64.b64encode(digest)
    hash: str = hash_alg + "-" + b64.decode(encoding="ascii")
    return hash


def get_csrf_token(session) -> str:
    token: Optional[str] = session.get("csrf_token", None)
    if token is None:
        csrf_token: str = secrets.token_urlsafe()
        session["csrf_token"] = csrf_token
        return csrf_token
    else:
        return token
