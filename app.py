"""Entry Point of the website
"""

import flask

app = flask.Flask(__name__)


@app.get("/")
@app.get("/index.html")
def index() -> str:
    """index.html for site"""
    return flask.render_template(
        "index.html",
        saved_items=[],
        recent_items=[],
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


if __name__ == "__main__":
    app.run(debug=True)
