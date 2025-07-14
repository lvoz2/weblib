"""Entry Point of the website
"""

import flask
from src import db

app = flask.Flask(__name__)


# The saved/recent items here are test items


@app.get("/")
@app.get("/index.html")
def index() -> str:
    """index.html for site"""
    return flask.render_template(
        "index.html",
        saved_items=[db.get_item(1, 1)],
        recent_items=[db.get_item(1, 1)],
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
def token() -> dict[str, bool]:
    json: dict[str, str | dict[str, str]] = flask.request.json
    platform = json["platform"]
    platform_id = json["platform_id"]
    user = db.get_or_create_user(platform, platform_id)
    if isinstance(user, db.User):
        # Everything is good
        return {"status": True}
    else:
        # Something bad happened
        print(e)
        return {"status": False, "error": e}


@app.post("/api/item/save")
def save_item() -> dict[str, bool | str]:
    try:
        item_id: int = flask.request.json["item_id"]
        user_id: int = flask.session["user_id"]
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
        user_id: int = flask.session["user_id"]
        msg = db.unsave_item(item_id, user_id)
        if msg is None:
            return {"status": True}
        return {"status": False, "error": msg}
    except Exception as e:
        print(e)
        return {"status": False, "error": str(e)}


@app.get("/api/item/save")
def get_saved() -> dict[str, list[dict[str, str | bool | int | dict[str, str]]]]:
    pass


if __name__ == "__main__":
    app.run(debug=True)
