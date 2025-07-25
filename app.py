"""Entry Point of the website"""

import json
import pathlib
from typing import Optional
from urllib import parse
import flask
import flask_sqlalchemy
import flask_session
import requests
from src import db

app = flask.Flask(__name__, instance_path=str(pathlib.Path().absolute()))

# Flask-Session setup
flask_sql_db = flask_sqlalchemy.SQLAlchemy(model_class=db.Base)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///server.db"
flask_sql_db.init_app(app)
app.config["SESSION_TYPE"] = "sqlalchemy"
app.config["SESSION_SQLALCHEMY"] = flask_sql_db
flask_session.Session(app)


@app.get("/")
@app.get("/index.html")
def index() -> str:
    """index.html for site"""
    user_id: Optional[int] = flask.session.get("user_id", None)
    saved_items = None if user_id is None else db.get_saved_items(user_id)
    logged_in: bool = user_id is not None
    return flask.render_template(
        "index.html",
        saved_items=saved_items,
        recent_items=[db.get_item(1, user_id)],
        logged_in=logged_in
    )


@app.get("/browse")
def browse() -> str:
    """browse page for site"""
    logged_in: bool = flask.session.get("user_id", None) is not None
    return flask.render_template(
        "browse.html",
        filters=[
            {
                "title": "Source",
                "radio_id": "sourceRadio",
                "name": "source",
                "default": "wikipedia",
                "type": "radio",
                "options": [
                    {"radio_id": "wikipedia", "name": "Wikipedia"},
                    {"radio_id": "openLib", "name": "Open Library"},
                    {"radio_id": "gbooks", "name": "Google Books"},
                ],
            }
        ],
        logged_in=logged_in
    )


@app.get("/query")
def query_page() -> str:
    """ask question page for site"""
    logged_in: bool = flask.session.get("user_id", None) is not None
    return flask.render_template("query.html", logged_in=logged_in)


@app.get("/saved")
def saved() -> str:
    """saved items page for site"""
    user_id: Optional[int] = flask.session.get("user_id", None)
    logged_in: bool = user_id is not None
    saved_items = None if user_id is None else db.get_saved_items(user_id)
    return flask.render_template("saved.html", saved_items=saved_items, logged_in=logged_in)


@app.post("/api/browse/search")
def search() -> dict[str, bool | str | list[dict[str, str | bool | int | dict[str, str]]]]:
    user_id: Optional[int] = flask.session.get("user_id", None)
    data = flask.request.json
    if data is None:
        return {"status": False, "error": "No data provided"}
    filters = data["filters"]
    num_results: int = data["num_results"]
    query: str = parse.quote(data["query"])
    if query == "":
        return {"status": False, "error": "Query must not be empty"}
    results = []
    match filters["source"]:
        case "wikipedia":
            api_url = "https://en.wikipedia.org/w/api.php?"
            url = (
                f"{api_url}action=query&format=json&list=search&formatversion=2&"
                + f"srsearch={query}&srlimit={num_results}"
            )
            headers = {"User-Agent": "WebLib/1.0 (https://github.com/lvoz2/weblib)"}
            response = requests.get(url, headers=headers, timeout=5.0)
            pages = response.json()["query"]["search"]
            page_ids = []
            items = {}
            for page in pages:
                item: Optional[dict[str, str | bool | int | dict[str, str]]] = (
                    db.get_item_by_source("Wikipedia", page["pageid"], user_id)
                )
                page_id: str = str(page["pageid"])
                if item is None:
                    page_ids.append(page_id)
                else:
                    items[page_id] = item
            if len(page_ids) != 0:
                page_ids_url = "|".join(page_ids)
                info_res = requests.get(
                    f"{api_url}action=query&prop=info&inprop=url&format=json&"
                    + f"pageids={page_ids_url}",
                    headers=headers, timeout=5.0
                )
                thumb_res = requests.get(
                    f"{api_url}action=query&prop=pageimages&piprop=name|thumbnail&"
                    + f"pithumbsize=200&format=json&pageids={page_ids_url}",
                    headers=headers, timeout=5.0
                )
                extract_res = requests.get(
                    "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&"
                    + f"explaintext&exintro&format=json&pageids={page_ids_url}",
                    headers=headers, timeout=5.0
                )
                info_json = info_res.json()["query"]["pages"]
                thumb_json = thumb_res.json()["query"]["pages"]
                extract_json = extract_res.json()["query"]["pages"]
            for page in pages:
                page_id = str(page["pageid"])
                if page_id in page_ids:
                    has_thumb = "thumbnail" in thumb_json[page_id].keys()
                    try:
                        # Smaller than the minimum
                        thumb_height = -1
                        thumb_mime = ""
                        if has_thumb:
                            thumb_url = thumb_json[page_id]["thumbnail"]["source"]
                            thumb_mime = (
                                requests.head(thumb_url, headers=headers, timeout=5.0)
                            ).headers["content-type"]
                            thumb_height = thumb_json[page_id]["thumbnail"]["height"]
                        # Clamps to 0-135px max img height. If no img, should be 0
                        thumb_height = max(0, min(135, thumb_height))
                        wiki_result = {
                            "title": page["title"],
                            "description": extract_json[page_id]["extract"],
                            "thumb_url": thumb_url if has_thumb else "",
                            "thumb_mime": (thumb_mime if has_thumb else ""),
                            "thumb_height": thumb_height,
                            "source_url": info_json[page_id]["fullurl"],
                            "source_name": "Wikipedia",
                            "source_id": page["pageid"],
                        }
                        wiki_result["id"] = db.create_item(wiki_result)
                        results.append(wiki_result)
                    except KeyError as e:
                        print(e)
                        print(thumb_json[page_id])
                else:
                    results.append(items[page_id])
        case "gbooks":
            pass
        case "openLib":
            pass
        case _:
            raise ValueError("Source filter not in list of allowed values")
    return {"status": True, "results": results}


@app.get("/api/oidc/redirect")
def redirect() -> str:
    return flask.render_template("redirect.html")


@app.post("/api/users/login")
def send() -> dict[str, bool | str | Optional[list[dict[str, str | bool | int | dict[str, str]]]]]:
    try:
        data: Optional[dict[str, str | dict[str, str]]] = flask.request.json
        if data is None:
            return {"status": False, "error": "No data provided"}
        email: Optional[str] = str(data["email"]) if "email" in data else None
        name: Optional[str] = str(data["name"]) if "name" in data else None
        username: Optional[str] = str(data["username"]) if "username" in data else None
        platform: Optional[str] = str(data["platform"]) if "platform" in data else None
        platform_id: Optional[dict[str, str] | str] = (
            data["platform_id"] if "platform_id" in data else None
        )
        if isinstance(platform_id, str):
            return {
                "status": False,
                "error": "platform_id must be provided as an object with key-value pairs",
            }
        if email is None:
            return {"status": False, "error": "No email provided"}
        if platform is None:
            return {"status": False, "error": "No platform provided"}
        if platform_id is None:
            return {"status": False, "error": "No platform_id provided"}
        user = db.get_or_create_user(
            email, platform, platform_id, name=name, username=username
        )
        app.session_interface.regenerate(flask.session)
        flask.session["user_id"] = user.id
        try:
            saved_items: Optional[list[dict[str, str | bool | int | dict[str, str]]]] = db.get_saved_items(user.id)
        except ValueError as e:
            return {"status": False, "error": "Failed to properly login"}
        return {"status": True, "saved": saved_items}
    except Exception as e:
        # Something bad happened
        print(e)
        return {"status": False, "error": str(e)}


@app.get("/api/users/logout")
def logout() -> dict[str, bool | str]:
    try:
        user_id: Optional[int] = flask.session.get("user_id", None)
        if user_id is None:
            return {"status": False, "error": "You must login to logout"}
        flask.session.clear()
        return {"status": True}
    except Exception as e:
        return {"status": False, "error": str(e)}


@app.post("/api/item/save")
def save_item() -> dict[str, bool | str]:
    try:
        data = flask.request.json
        if data is None:
            return {"status": False, "error": "No data provided"}
        item_id: Optional[int] = int(data["item_id"]) if "item_id" in data else None
        user_id: Optional[int] = flask.session.get("user_id", None)
        if user_id is None:
            return {"status": False, "error": "Login to save items for later"}
        if item_id is None:
            return {"status": False, "error": "Provide an item_id to save"}
        msg = db.save_item(item_id, user_id)
        if msg is None:
            return {"status": True}
        return {"status": False, "error": msg}
    except Exception as e:
        print(e)
        return {"status": False, "error": str(e)}


@app.post("/api/item/unsave")
def unsave_item() -> dict[str, bool | str]:
    try:
        data = flask.request.json
        if data is None:
            return {"status": False, "error": "No data provided"}
        item_id: Optional[int] = int(data["item_id"]) if "item_id" in data else None
        user_id: Optional[int] = flask.session.get("user_id", None)
        if user_id is None:
            return {"status": False, "error": "Login to unsave items"}
        if item_id is None:
            return {"status": False, "error": "Provide an item_id to unsave"}
        msg = db.unsave_item(item_id, user_id)
        if msg is None:
            return {"status": True}
        return {"status": False, "error": msg}
    except Exception as e:
        print(e)
        return {"status": False, "error": str(e)}


if __name__ == "__main__":
    app.run(debug=True)
