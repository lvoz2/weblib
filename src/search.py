"""Collection of functions to search various 3rd-party sites"""

from typing import Optional
from urllib import parse

import requests
from src import db


def gbooks(
    query: str,
    num_results: int,
    filters: dict[str, str],
    *,
    user_id: Optional[int] = None,
) -> list[dict[str, str | bool | int]]:
    quoted_query: str = parse.quote_plus(query, safe=":")
    results: list[dict[str, str | bool | int]] = []
    api_url = "https://www.googleapis.com/books/v1/volumes?"
    url: str = (
        f"{api_url}q={quoted_query}&maxResults={num_results}"
        + ("&download=" + filters["download"] if filters["download"] != "none" else "")
        + f"&filter={filters['available']}&printType={filters['print']}"
    )
    print(url)
    headers = {"User-Agent": "WebLib/1.0 (https://github.com/lvoz2/weblib) (gzip)"}
    res: dict[
        str,
        str
        | int
        | list[
            dict[
                str,
                str
                | dict[
                    str,
                    str
                    | int
                    | bool
                    | list[str]
                    | list[dict[str, str]]
                    | dict[str, str]
                    | dict[str, bool],
                ],
            ]
        ],
    ] = (requests.get(url, headers=headers, timeout=10.0)).json()
    volumes: list[
        dict[
            str,
            str
            | dict[
                str,
                str
                | int
                | bool
                | list[str]
                | list[dict[str, str]]
                | dict[str, str]
                | dict[str, bool],
            ],
        ]
    ] = (
        (res["items"] if isinstance(res["items"], list) else [])
        if "items" in res
        else []
    )
    volumes.reverse()
    for volume in volumes:
        vol_id: Optional[str] = (
            (volume["id"] if isinstance(volume["id"], str) else None)
            if "id" in volume
            else None
        )
        vol_info: Optional[
            dict[
                str,
                str
                | int
                | bool
                | list[str]
                | list[dict[str, str]]
                | dict[str, str]
                | dict[str, bool],
            ]
        ] = (
            (volume["volumeInfo"] if isinstance(volume["volumeInfo"], dict) else None)
            if "volumeInfo" in volume
            else None
        )
        if vol_id is not None and vol_info is not None:
            item: Optional[dict[str, str | bool | int]] = db.get_item_by_source(
                "Google Books", vol_id, user_id, add_to_recent_search=True
            )
            if item is None:
                # Haven't stored item metadata yet
                description: str = (
                    (
                        "By "
                        + ", ".join(
                            [
                                (author if isinstance(author, str) else "")
                                for author in vol_info["authors"]
                            ]
                        )
                        if isinstance(vol_info["authors"], list)
                        else ""
                    )
                    if "authors" in vol_info
                    else ""
                ) + (
                    f". {vol_info['description']}" if "description" in vol_info else ""
                )
                thumb: dict[str, str] = {"url": "", "mime": ""}
                # Apparently this walrus will still exist outside the scope of the if
                if has_thumb := (
                    (
                        "thumbnail" in vol_info["imageLinks"]
                        if isinstance(vol_info["imageLinks"], dict)
                        else False
                    )
                    if "imageLinks" in vol_info
                    else False
                ):
                    potential_url = (
                        vol_info["imageLinks"]["thumbnail"]
                        if isinstance(vol_info["imageLinks"], dict)
                        and "thumbnail" in vol_info["imageLinks"]
                        else ""
                    )
                    thumb["url"] = (
                        potential_url if isinstance(potential_url, str) else ""
                    )
                    thumb["mime"] = (
                        requests.head(thumb["url"], headers=headers, timeout=5.0)
                    ).headers["content-type"]
                title: str = (
                    vol_info["title"]
                    if "title" in vol_info and isinstance(vol_info["title"], str)
                    else ""
                )
                source_url: str = (
                    vol_info["infoLink"]
                    if "infoLink" in vol_info and isinstance(vol_info["infoLink"], str)
                    else ""
                )
                volume_data: dict[str, str | int] = {
                    "title": title,
                    "description": description,
                    "thumb_url": thumb["url"] if has_thumb else "",
                    "thumb_mime": (thumb["mime"] if has_thumb else ""),
                    "thumb_height": 135,
                    "source_url": source_url,
                    "source_name": "Google Books",
                    "source_id": vol_id,
                }
                results.append(
                    db.create_item(volume_data, user_id, add_to_recent_search=True)
                )
            else:
                # Have got item metadata
                results.append(item)
    results.reverse()
    return results


def wikipedia(
    query: str,
    num_results: int,
    *,
    user_id: Optional[int] = None,
) -> list[dict[str, str | bool | int]]:
    """Function to search Wikipedia
    query(str): the search query
    num_results(int): how many results to return
    kwargs:
    user_id(int | None): the user_id, to check if returned items are saved or not"""
    quoted_query: str = parse.quote(query)
    results: list[dict[str, str | bool | int]] = []
    api_url = "https://en.wikipedia.org/w/api.php?"
    url = (
        f"{api_url}action=query&format=json&list=search&formatversion=2&"
        + f"srsearch={quoted_query}&srlimit={num_results}"
    )
    headers = {"User-Agent": "WebLib/1.0 (https://github.com/lvoz2/weblib)"}
    response = requests.get(url, headers=headers, timeout=10.0)
    pages = response.json()["query"]["search"]
    page_ids = []
    items = {}
    correct_order = [str(page["pageid"]) for page in pages]
    # Reversals for correct recently searched ordering
    pages.reverse()
    for page in pages:
        page_id: str = str(page["pageid"])
        item: Optional[dict[str, str | bool | int]] = db.get_item_by_source(
            "Wikipedia", page_id, user_id
        )
        if item is None:
            page_ids.append(page_id)
        else:
            items[page_id] = item
    if len(page_ids) != 0:
        page_ids_url = "|".join(page_ids)
        info_res = requests.get(
            f"{api_url}action=query&prop=info&inprop=url&format=json&"
            + f"pageids={page_ids_url}",
            headers=headers,
            timeout=5.0,
        )
        thumb_res = requests.get(
            f"{api_url}action=query&prop=pageimages&piprop=name|thumbnail&"
            + f"pithumbsize=200&format=json&pageids={page_ids_url}",
            headers=headers,
            timeout=5.0,
        )
        extract_res = requests.get(
            "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&"
            + f"explaintext&exintro&format=json&pageids={page_ids_url}",
            headers=headers,
            timeout=5.0,
        )
        info_json = info_res.json()["query"]["pages"]
        thumb_json = thumb_res.json()["query"]["pages"]
        extract_json = extract_res.json()["query"]["pages"]
    for page in pages:
        page_id = str(page["pageid"])
        if page_id in page_ids:
            has_thumb = "thumbnail" in thumb_json[page_id].keys()
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
                "source_id": page_id,
            }
            results.append(
                db.create_item(wiki_result, user_id, add_to_recent_search=True)
            )
        else:
            results.append(items[page_id])
            # So cached results arent behind new results in recent search list
            db.get_item_by_source(
                "Wikipedia", page_id, user_id, add_to_recent_search=True
            )
    return sorted(
        results,
        key=lambda item: correct_order.index(
            item["source_id"] if isinstance(item["source_id"], str) else ""
        ),
    )
