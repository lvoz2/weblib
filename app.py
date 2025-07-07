"""Entry Point of the website
"""

import flask

app = flask.Flask(__name__)

@app.get("/")
@app.get("/index.html")
def index():
    """index.html for site
    """
    return flask.render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
