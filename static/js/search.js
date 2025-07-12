import { wrapCards, createCard } from "./card.js";

function init() {
    document.getElementById("searchBtn").addEventListener("click", search)
}

async function search(e) {
    const query = document.getElementById("searchBox").value;
    const json = (await fetch("/api/browse/search", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            "query": query
        })
    }).then(res => res.json()).then(json => {
        return json;
    })).result;
    const resultsE = document.getElementById("resultsInner");
    resultsE.innerHTML = "";
    for (const item of json) {
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