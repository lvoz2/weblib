"use strict";

export function wrapCard(e) {
    const child = e.children[0];
    const parentHeight = e.clientHeight;
    const childHeight = child.clientHeight;
    const styles = window.getComputedStyle(child);
    const lines = Math.floor(parentHeight / (childHeight / styles["-webkit-line-clamp"]));
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

export function wrapCards () {
    document.querySelectorAll(".card-description").forEach((e) => {
        wrapCard(e)
        // From MDN: https://developer.mozilla.org/en-US/docs/Web/API/ResizeObserver
        const resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                wrapCard(entry.target)
            }
        });
        resizeObserver.observe(e);
    });
}

export async function toggleSave(e) {
    let target = e.target;
    if (target.innerHTML.length === 0) {
        target = target.parentElement;
    }
    const itemId = target.parentElement.parentElement.parentElement.dataset.id;
    const saveIcons = document.querySelectorAll(".card[data-id='" + itemId + "'] .save-icons");
    for (let saveIcon of saveIcons) {
        for (let child of saveIcon.children) {
            child.classList.toggle("hidden");
        }
    }
    if (target.querySelectorAll(".hidden")[0].classList.contains("fa-solid")) {
        // Item is now not saved
        const msg = await (await fetch("/api/item/unsave", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                "item_id": itemId
            })
        })).json();
        if (!msg.status) {
            alert("An issue happened during unsave. Please notify site owner, sending them this error message: " + json.error);
            return;
        }
    } else {
        // Item is now saved
        if (location.pathname === "/") {
            const card = target.parentElement.parentElement.parentElement;
            const savedListE = document.querySelectorAll("#saved .item-list")[0];
            prependCard(card, savedListE)
        }
        const msg = await (await fetch("/api/item/save", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                "item_id": itemId
            })
        })).json();
        if (!msg.status) {
            alert("An issue happened during save. Please notify site owner, sending them this error message: " + json.error);
            return;
        }
    }
}

function prependCard(card, listE) {
    if (location.pathname === "/") {
        if (card === listE.children[0]) {
            // Card already first, do nothing
            return;
        }
        // Remove cards with the same id already in the list
        listE.querySelectorAll(".card[data-id='" + card.dataset.id + "']").forEach((cur) => {
            cur.remove();
        });
        const newCard = card.cloneNode(true);
        newCard.querySelectorAll(".card").forEach((e) => {
            e.addEventListener("click", clickCard);
        });
        newCard.querySelectorAll(".save-icons").forEach((e) => {
            e.addEventListener("click", toggleSave);
        });
        listE.prepend(newCard);
        // Can't use listE.childNodes (even though both produce NodeLists) because it will update as I mutate
        listE.querySelectorAll(".card").forEach((cur, i) => {
            if (i >= 20) {
                cur.remove();
            }
        });
    }
}

function clickCard(e) {
    let el = e.target;
    while(!(el.classList.contains("card") || el.classList.contains("save-icons"))) {
        el = el.parentElement;
    }
    if (el.classList.contains("card")) {
        prependCard(el, document.querySelectorAll("#recentView .item-list")[0]);
        fetch("/api/recent/viewed", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                item_id: el.dataset.id
            })
        });
        window.open(el.dataset.href, "_blank");
    }
}

export function createCard(item) {
    const cardHTML = `<div class="card" data-id="` + item.id + `" data-href="` + item.source_url + `">
        <img src="` + item.thumb_url + `" width="200px" height="` + item.thumb_height +`px">
        <div class="card-inner-box">
            <div class="card-inner-top">
                <h3>` + item.title + `</h3>
                <div class="save-icons">
                    <i class="save-icon` + (item.saved ? " hidden" : "") + ` save-icon-border save-icon-first fa-regular fa-bookmark"></i>
                    <i class="save-icon` + (item.saved ? "" : " hidden") + ` save-icon-fill fa-solid fa-bookmark"></i>
                </div>
            </div>
            <div class="card-description">
                <p>` + item.description + `</p>
            </div>
        </div>
        <div class="card-source">
            <p>Source: <a href="` + item.source_url + '">' + item.source_name + `</a></p>
        </div>
    </div>`;
    const div = document.createElement("div");
    div.innerHTML = cardHTML.trim();
    window.div = div;
    div.querySelectorAll(".card").forEach((e) => {
        e.addEventListener("click", clickCard);
    });
    div.querySelectorAll(".save-icons").forEach((e) => {
        e.addEventListener("click", toggleSave);
    });
    return div.children[0];
}


export function init() {
    document.querySelectorAll(".card").forEach((e) => {
        e.addEventListener("click", clickCard);
    });
    document.querySelectorAll(".save-icons").forEach((e) => {
        e.addEventListener("click", toggleSave);
    });
}

export default { wrapCard, wrapCards, toggleSave, createCard, init };
