"""Entry Point of the website"""

import json
import pathlib
from typing import Optional

import flask
import flask_session
import flask_sqlalchemy
from src import db
from src import search as search_funcs

app = flask.Flask(__name__, instance_path=str(pathlib.Path().absolute()))

# Flask-Session setup
flask_sql_db = flask_sqlalchemy.SQLAlchemy(model_class=db.Base)
db.setup_db()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///server.db"
flask_sql_db.init_app(app)
app.config["SESSION_TYPE"] = "sqlalchemy"
app.config["SESSION_SQLALCHEMY"] = flask_sql_db
flask_session.Session(app)

with open("src/filters.json", "r", encoding="utf-8") as f:
    filter_control = json.load(f)["filters"]


@app.get("/")
@app.get("/index.html")
def index() -> str:
    """index.html for site"""
    user_id: Optional[int] = flask.session.get("user_id", None)
    saved_items = None if user_id is None else db.get_saved_items(user_id)[:20]
    logged_in: bool = user_id is not None
    return flask.render_template(
        "index.html",
        saved_items=saved_items,
        recent_items=db.get_recently_viewed(user_id),
        recent_search_items=db.get_recently_searched(user_id),
        logged_in=logged_in,
    )


@app.get("/browse")
def browse() -> str:
    """browse page for site"""
    logged_in: bool = flask.session.get("user_id", None) is not None
    return flask.render_template(
        "browse.html",
        filters=filter_control,
        logged_in=logged_in,
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
    return flask.render_template(
        "saved.html", saved_items=saved_items, logged_in=logged_in
    )


@app.post("/api/browse/search")
def search() -> dict[str, bool | str | list[dict[str, str | bool | int]]]:
    user_id: Optional[int] = flask.session.get("user_id", None)
    data = flask.request.json
    if data is None:
        return {"status": False, "error": "No data provided"}
    filters: Optional[dict[str, str]] = data["filters"] if "filters" in data else None
    if filters is None:
        return {"status": False, "error": "No filters provided"}
    num_results: int = min(data["num_results"], 20)
    query: str = data["query"]
    results: list[dict[str, str | bool | int]] = []
    if query == "":
        return {"status": True, "results": results}
    match filters["source"]:
        case "wikipedia":
            results = search_funcs.wikipedia(query, num_results, user_id=user_id)
        case "gbooks":
            results = search_funcs.gbooks(query, num_results, filters, user_id=user_id)
        case "openLib":
            pass
        case _:
            raise ValueError("Source filter not in list of allowed values")
    return {"status": True, "results": results}


@app.get("/api/oidc/redirect")
def redirect() -> str:
    return flask.render_template("redirect.html")


@app.post("/api/users/login")
def send() -> dict[str, bool | str | Optional[list[dict[str, str | bool | int]]]]:
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
                "error": "platform_id must be provided as an object with "
                + "key-value pairs",
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
        if not isinstance(user["id"], int):
            raise TypeError("User id somehow not an int")
        flask.session["user_id"] = user["id"]
        try:
            saved_items: Optional[list[dict[str, str | bool | int]]] = (
                db.get_saved_items(user["id"])
            )
        except ValueError:
            return {"status": False, "error": "Failed to properly login"}
        return {
            "status": True,
            "saved": saved_items,
            "recently_viewed": db.get_recently_viewed(user["id"]),
            "recently_searched": db.get_recently_searched(user["id"]),
        }
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
        return {"status": False, "error": str(e)}


@app.post("/api/recent/viewed")
def add_to_recent_viewed() -> dict[str, bool | str]:
    try:
        data: Optional[dict[str, str]] = flask.request.json
        if data is None:
            return {"status": False, "error": "No data provided"}
        item_id: Optional[int] = int(data["item_id"]) if "item_id" in data else None
        user_id: Optional[int] = flask.session.get("user_id", None)
        if user_id is None:
            return {"status": False, "error": "Login to remember recent items"}
        if item_id is None:
            return {
                "status": False,
                "error": "Provide an item_id to remember recent items",
            }
        msg = db.append_to_recently_viewed(user_id, item_id)
        if msg is None:
            return {"status": True}
        return {"status": False, "error": msg}
    except Exception as e:
        return {"status": False, "error": str(e)}


if __name__ == "__main__":
    app.run(debug=True)
