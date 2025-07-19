"""Entry Point of the website
"""

import pathlib
import flask
import flask_sqlalchemy
import flask_session
from typing import Optional
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
    return flask.render_template("browse.html")


@app.get("/query")
def query() -> str:
    """ask question page for site"""
    return flask.render_template("query.html")


@app.get("/saved")
def saved() -> str:
    """saved items page for site"""
    return flask.render_template("saved.html")


@app.post("/api/browse/search")
def search() -> dict[str, list[dict[str, str | bool | int | dict[str, str]]]]:
    json = flask.request.json
    print(json)
    return {"result": [db.get_item(1, 1)]}


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
