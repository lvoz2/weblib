"use strict";

import { wrapCards, createCard } from "./card.js";

function showFilters() {
    const el = document.querySelectorAll(".filter-options[name=source]")[0];
    const val = el.elements.namedItem("source").value;
    document.querySelectorAll(".filter-section").forEach((e) => {
        const desiredSource = e.dataset.shownSource;
        if (desiredSource == undefined || desiredSource === val) {
            e.classList.remove("hidden");
        } else {
            e.classList.add("hidden");
        }
    });
}

function init() {
    document.getElementById("searchBtn").addEventListener("click", search);
    document.getElementById("resultsSlider").addEventListener("input", resultsSlider);
    document.querySelectorAll(".filter-options[name=source]")[0].addEventListener("input", showFilters);
    showFilters();
}


async function search(e) {
    const query = document.getElementById("searchBox").value;
    const filterEs = document.querySelectorAll(".filter-options");
    let filterData = {};
    for (let filterE of filterEs) {
        switch (filterE.dataset.type) {
            case "radio":
                filterData[filterE.name] = filterE.elements.namedItem(filterE.name).value;
                break;
        }
    }
    if (filterData.source === "wiktionary" || filterData.source === "openLib") {
        alert("This search source is not implemented yet! Please use something else.")
        return
    }
    const num_results = parseInt(document.getElementById("resultsSliderLabel").innerText);
    const json = await fetch("/api/browse/search", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            "query": query,
            num_results: num_results,
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

function resultsSlider(e) {
    e.target.nextElementSibling.children[0].innerText = e.target.value;
}

if (document.readyState !== "loading") {
    init()
} else {
    document.addEventListener("DOMContentLoaded", init);
}