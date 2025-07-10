"""Entry Point of the website
"""

import flask

app = flask.Flask(__name__)


# The saved/recent items here are test items


@app.get("/")
@app.get("/index.html")
def index() -> str:
    """index.html for site"""

    return flask.render_template(
        "index.html",
        saved_items=[
            {
                "id": "717de6c1-32da-4001-b9a3-6378f4a38c64",
                "title": "Australia",
                "description": "Australia, officially the Commonwealth of Australia, "
                + "is a country comprising the mainland of the Australian continent, "
                + "the island of Tasmania and numerous smaller islands. It has a "
                + "total area of 7,688,287 km2 (2,968,464 sq mi), making it the "
                + "sixth-largest country in the world and the largest in Oceania. "
                + "Australia is the world's flattest and driest inhabited continent. "
                + "It is a megadiverse country, and its size gives it a wide variety "
                + "of landscapes and climates including deserts in the interior and "
                + "tropical rainforests along the coast. ",
                "thumb_ext": "svg",
                "thumb_mime": "image/svg+xml",
                "saved": True,
                "source": {
                    "url": "https://en.wikipedia.org/wiki/Australia",
                    "name": "Wikipedia",
                },
            }
        ],
        recent_items=[
            {
                "id": "717de6c1-32da-4001-b9a3-6378f4a38c64",
                "title": "Australia",
                "description": "Australia, officially the Commonwealth of Australia, "
                + "is a country comprising the mainland of the Australian continent, "
                + "the island of Tasmania and numerous smaller islands. It has a "
                + "total area of 7,688,287 km2 (2,968,464 sq mi), making it the "
                + "sixth-largest country in the world and the largest in Oceania. "
                + "Australia is the world's flattest and driest inhabited continent. "
                + "It is a megadiverse country, and its size gives it a wide variety "
                + "of landscapes and climates including deserts in the interior and "
                + "tropical rainforests along the coast. ",
                "thumb_ext": "svg",
                "thumb_mime": "image/svg+xml",
                "saved": True,
                "source": {
                    "url": "https://en.wikipedia.org/wiki/Australia",
                    "name": "Wikipedia",
                },
            }
        ],
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
def search() -> dict[str, list[dict[str, str | bool | dict[str, str]]]]:
    json = flask.request.json
    print(json)
    return {
        "result": [
            {
                "id": "717de6c1-32da-4001-b9a3-6378f4a38c64",
                "title": "Australia",
                "description": "Australia, officially the Commonwealth of Australia, "
                + "is a country comprising the mainland of the Australian continent, "
                + "the island of Tasmania and numerous smaller islands. It has a "
                + "total area of 7,688,287 km2 (2,968,464 sq mi), making it the "
                + "sixth-largest country in the world and the largest in Oceania. "
                + "Australia is the world's flattest and driest inhabited continent. "
                + "It is a megadiverse country, and its size gives it a wide variety "
                + "of landscapes and climates including deserts in the interior and "
                + "tropical rainforests along the coast. ",
                "thumb_ext": "svg",
                "thumb_mime": "image/svg+xml",
                "saved": True,
                "source": {
                    "url": "https://en.wikipedia.org/wiki/Australia",
                    "name": "Wikipedia",
                },
            }
        ]
    }


if __name__ == "__main__":
    app.run(debug=True)
