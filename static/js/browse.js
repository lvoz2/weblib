if (!window.app) {
    window.app = {};
}

window.app.init = function() {
    document.getElementById("searchBtn").addEventListener("click", window.app.search)
}

window.app.search = async function(e) {
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
    for (item of json) {
        console.log(item);
        const cardHTML = `<div class="card">
            <img src="/static/cache/` + item.id + "/thumb." + item.thumb_ext + `">
            <div class="card-inner-box">
                <div class="card-inner-top">
                    <h3>` + item.title + `</h3>
                    <div class="save-icons">
                        <i class="save-icon ` + (!item.saved ? "hidden" : "") + ` save-icon-first fa-solid fa-bookmark parent-styled"></i>
                        <i class="save-icon ` + (!item.saved ? "hidden" : "") + ` fa-regular fa-bookmark parent-styled"></i>
                    </div>
                </div>
                <div class="card-description">
                    <p>` + item.description + `</p>
                </div>
            </div>
            <div class="card-source">
                <p>Source: <a href="` + item.source.url + '">' + item.source.name + `</a></p>
            </div>
        </div>`;
        resultsE.innerHTML += cardHTML;
    }
    window.app.wrapCards()
}

if (document.readyState !== "loading") {
    window.app.init()
} else {
    document.addEventListener("DOMContentLoaded", window.app.init);
}

window.app.wrapCard = function(e) {
    const child = e.children[0];
    const parentHeight = e.clientHeight;
    const childHeight = child.clientHeight;
    const styles = window.getComputedStyle(child);
    const lines = Math.floor(parentHeight / (childHeight / styles["-webkit-line-clamp"]));
    console.log(lines);
    if (lines === 0 || lines == Infinity) {
        child.style["display"] = "none";
        child.style["-webkit-line-clamp"] = 1;
        child.style["line-clamp"] = 1;
    } else {
        child.style["display"] = "-webkit-box";
        child.style["-webkit-line-clamp"] = lines;
        child.style["line-clamp"] = lines;
    }
}

window.app.wrapCards = function() {
    cardInners = document.querySelectorAll(".card-description").forEach((e) => {
        window.app.wrapCard(e)
        // From MDN: https://developer.mozilla.org/en-US/docs/Web/API/ResizeObserver
        const resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                window.app.wrapCard(entry.target)
            }
        });
        resizeObserver.observe(e);
    });
}