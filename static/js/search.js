"use strict";

import { wrapCards, createCard } from "./card.js";

function init() {
    document.getElementById("searchBtn").addEventListener("click", search)
}


async function search(e) {
    const query = document.getElementById("searchBox").value;
    const filterEs = document.querySelectorAll(".filter-options");
    let filterData = {};
    for (let filterE of filterEs) {
        switch (filterE.dataset.type) {
            case "radio":
                filterData[filterE.name] = filterE.elements.namedItem("source").value;
                break;
        }
    }
    const json = await fetch("/api/browse/search", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            "query": query,
            num_results: 5,
            filters: filterData
        })
    }).then(res => res.json()).then(json => {
        return json;
    });
    if (!Object.hasOwnProperty.call(json, "results")) {
        throw new Error("Results not in API response");
    }
    const resultsE = document.getElementById("resultsInner");
    resultsE.innerHTML = "";
    for (const item of json.results) {
        const card = createCard(item);
        resultsE.append(card);
    }
    wrapCards()
}

if (document.readyState !== "loading") {
    init()
} else {
    document.addEventListener("DOMContentLoaded", init);
}