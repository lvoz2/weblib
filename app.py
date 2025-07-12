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


if __name__ == "__main__":
    app.run(debug=True)
