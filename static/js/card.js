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

export function toggleSave(e) {
    let target = e.target;
    if (target.innerHTML.length === 0) {
        target = target.parentElement;
    }
    for (let child of target.children) {
        child.classList.toggle("hidden");
    }
}

export function createCard(item) {
    const cardHTML = `<div class="card">
        <img src="/static/cache/` + item.id + "/thumb." + item.thumb_ext + `" width="200px" height="` + item.thumb_height +`px">
        <div class="card-inner-box">
            <div class="card-inner-top">
                <h3>` + item.title + `</h3>
                <div class="save-icons">
                    <i class="save-icon ` + (item.saved ? "" : "hidden") + ` save-icon-first fa-solid fa-bookmark parent-styled"></i>
                    <i class="save-icon ` + (item.saved ? "hidden" : "") + ` fa-regular fa-bookmark parent-styled"></i>
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
    const div = document.createElement("div");
    div.className = "card";
    div.innerHTML = cardHTML.trim();
    window.div = div;
    div.querySelectorAll(".save-icons").forEach((e) => {
        e.addEventListener("click", toggleSave);
    });
    return div.children[0];
}

export function init() {
    document.querySelectorAll(".save-icons").forEach((e) => {
        e.addEventListener("click", toggleSave);
    });
}

export default { wrapCard, wrapCards, toggleSave, createCard, init };