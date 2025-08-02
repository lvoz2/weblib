"use strict";

/*
 * Stumbled upon this recently. I've done some of its suggestions before, but its pretty neat
 * https://youmightnotneedjquery.com/
 */

import { init as cardInit } from "./card.js";

function init() {
    if (location.pathname === "/" || location.pathname === "/saved") {
        cardInit()
    }
}

if (document.readyState !== "loading") {
    init()
} else {
    document.addEventListener("DOMContentLoaded", init);
}
