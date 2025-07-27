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
) -> list[dict[str, str | bool | int | dict[str, str]]]:
    quoted_query: str = parse.quote_plus(query, safe=":")
    results: list[dict[str, str | bool | int | dict[str, str]]] = []
    api_url = "https://www.googleapis.com/books/v1/volumes?"
    url: str = (
        f"{api_url}q={quoted_query}&maxResults={num_results}"
        + ("&download=" + filters["download"] if filters["download"] != "none" else "")
        + f"&filter={filters['available']}&printType={filters['print']}"
    )
    headers = {"User-Agent": "WebLib/1.0 (https://github.com/lvoz2/weblib)"}
    volumes: list[
        dict[
            str,
            str
            | dict[
                str,
                str | int | bool | list[str | dict[str, str]] | dict[str, str | bool],
            ],
        ]
    ] = (requests.get(url, headers=headers, timeout=5.0)).json()["items"]
    for volume in volumes:
        vol_id: str = volume["id"]
        item: Optional[dict[str, str | bool | int | dict[str, str]]] = (
            db.get_item_by_source("Google Books", vol_id, user_id)
        )
        if item is None:
            # Haven't stored item metadata yet
            vol_info = volume["volumeInfo"]
            print(vol_info)
            description: str = f"By {', '.join(vol_info['authors'])}" + (
                f". {vol_info['description']}" if "description" in vol_info else ""
            )
            has_thumb = (
                "thumbnail" in vol_info["imageLinks"]
                if "imageLinks" in vol_info
                else False
            )
            thumb = {"url": "", "mime": ""}
            if has_thumb:
                thumb["url"] = vol_info["imageLinks"]["thumbnail"]
                thumb["mime"] = (
                    requests.head(thumb["url"], headers=headers, timeout=5.0)
                ).headers["content-type"]
            volume_data = {
                "title": vol_info["title"],
                "description": description,
                "thumb_url": thumb["url"] if has_thumb else "",
                "thumb_mime": (thumb["mime"] if has_thumb else ""),
                "thumb_height": 135,
                "source_url": vol_info["infoLink"],
                "source_name": "Google Books",
                "source_id": vol_id,
            }
            results.append(db.create_item(volume_data))
        else:
            # Have got item metadata
            results.append(item)
    return results


def wikipedia(
    query: str,
    num_results: int,
    filters: dict[str, str],
    *,
    user_id: Optional[int] = None,
) -> list[dict[str, str | bool | int | dict[str, str]]]:
    """Function to search Wikipedia
    query(str): the search query
    num_results(int): how many results to return
    kwargs:
    user_id(int | None): the user_id, to check if returned items are saved or not"""
    quoted_query: str = parse.quote(query)
    results: list[dict[str, str | bool | int | dict[str, str]]] = []
    api_url = "https://en.wikipedia.org/w/api.php?"
    url = (
        f"{api_url}action=query&format=json&list=search&formatversion=2&"
        + f"srsearch={quoted_query}&srlimit={num_results}"
    )
    headers = {"User-Agent": "WebLib/1.0 (https://github.com/lvoz2/weblib)"}
    response = requests.get(url, headers=headers, timeout=5.0)
    pages = response.json()["query"]["search"]
    page_ids = []
    items = {}
    for page in pages:
        page_id: str = str(page["pageid"])
        item: Optional[dict[str, str | bool | int | dict[str, str]]] = (
            db.get_item_by_source("Wikipedia", page_id, user_id)
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
                    "source_id": page_id,
                }
                wiki_result = db.create_item(wiki_result)
                results.append(wiki_result)
            except KeyError as e:
                print(e)
                print(thumb_json[page_id])
        else:
            results.append(items[page_id])
    return results
