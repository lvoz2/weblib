"""Entry Point of the website
"""

import json
import pathlib
import flask
import flask_sqlalchemy
import flask_session
import requests
from typing import Optional
from urllib import parse
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
    saved = None if user_id is None else db.get_saved_items(user_id)
    return flask.render_template(
        "index.html",
        saved_items=saved,
        recent_items=[db.get_item(1, user_id)],
    )


@app.get("/browse")
def browse() -> str:
    """browse page for site"""
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
    )


@app.get("/query")
def query() -> str:
    """ask question page for site"""
    return flask.render_template("query.html")


@app.get("/saved")
def saved() -> str:
    """saved items page for site"""
    return flask.render_template("saved.html")


@app.post("/api/browse/search")
def search() -> dict[str, str | list[dict[str, str | bool | int | dict[str, str]]]]:
    user_id: Optional[int] = flask.session.get("user_id", None)
    data = flask.request.json
    filters = json.loads(data["filters"])
    num_results: int = data["num_results"]
    query: str = parse.quote(data["query"])
    if query == "":
        return {"error": "Query must not be empty"}
    results = []
    match filters["source"]:
        case "wikipedia":
            api_url = "https://en.wikipedia.org/w/api.php?"
            url = (
                f"{api_url}action=query&format=json&list=search&formatversion=2&"
                + f"srsearch={query}&srlimit={num_results}"
            )
            headers = {"User-Agent": "WebLib/1.0 (https://github.com/lvoz2/weblib)"}
            response = requests.get(url, headers=headers)
            pages = response.json()["query"]["search"]
            page_ids = []
            items = {}
            for page in pages:
                item: Optional[dict[str, str | bool | int | dict[str, str]]] = (
                    db.get_item_by_source("Wikipedia", page["pageid"], user_id)
                )
                page_id: str = str(page["pageid"])
                if item is None:
                    print("not", page_id)
                    page_ids.append(page_id)
                else:
                    print("found", page_id)
                    items[page_id] = item
            if len(page_ids) != 0:
                page_ids_url = "|".join(page_ids)
                info_res = requests.get(
                    f"{api_url}action=query&prop=info&inprop=url&format=json&"
                    + f"pageids={page_ids_url}",
                    headers=headers,
                )
                thumb_res = requests.get(
                    f"{api_url}action=query&prop=pageimages&piprop=name|thumbnail&"
                    + f"pithumbsize=200&format=json&pageids={page_ids_url}",
                    headers=headers,
                )
                extract_res = requests.get(
                    "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&"
                    + f"explaintext&exintro&format=json&pageids={page_ids_url}",
                    headers=headers,
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
                        if has_thumb:
                            thumb_url = thumb_json[page_id]["thumbnail"]["source"]
                            thumb_headers = requests.head(thumb_url, headers=headers)
                            thumb_height = thumb_json[page_id]["thumbnail"]["height"]
                        # Clamps to 0-135px max img height. If no img, should be 0
                        thumb_height = max(0, min(135, thumb_height))
                        wiki_result = {
                            "title": page["title"],
                            "description": extract_json[page_id]["extract"],
                            "thumb_url": thumb_url if has_thumb else "",
                            "thumb_mime": (
                                thumb_headers.headers["content-type"]
                                if has_thumb
                                else ""
                            ),
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
    return {"results": results}


@app.get("/api/oidc/redirect")
def redirect() -> str:
    return flask.render_template("redirect.html")


@app.post("/api/users/send")
def send() -> dict[str, bool | Exception]:
    try:
        json: dict[str, str | dict[str, str]] = flask.request.json
        email = json["email"]
        name = json["name"] if "name" in json else None
        username = json["username"] if "username" in json else None
        platform = json["platform"]
        platform_id = json["platform_id"]
        user = db.get_or_create_user(
            email, platform, platform_id, name=name, username=username
        )
        app.session_interface.regenerate(flask.session)
        flask.session["user_id"] = user.id
        return {"status": True}
    except Exception as e:
        # Something bad happened
        print(e)
        return {"status": False, "error": e}


@app.post("/api/item/save")
def save_item() -> dict[str, bool | str]:
    try:
        item_id: int = flask.request.json["item_id"]
        user_id: Optional[int] = flask.session.get("user_id", None)
        if user_id is None:
            return {"status": False, "error": "Login to save items for later"}
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
        item_id: int = flask.request.json["item_id"]
        user_id: Optional[int] = flask.session.get("user_id", None)
        if user_id is None:
            return {"status": False, "error": "Login to unsave items"}
        msg = db.unsave_item(item_id, user_id)
        if msg is None:
            return {"status": True}
        return {"status": False, "error": msg}
    except Exception as e:
        print(e)
        return {"status": False, "error": str(e)}


if __name__ == "__main__":
    app.run(debug=True)
