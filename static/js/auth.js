"use strict";

import { wrapCards, createCard } from "./card.js";

const clientId = "21b089d7-aa3e-478f-a992-9aa757adc73f";
const redirectUri = encodeURIComponent(location.origin + "/api/oidc/redirect");
const scopes = encodeURIComponent(["openid", "email", "profile"].join(" "));

async function onMessage(e) {
    const data = e.data;
    window.data = e.data;
    if (Object.hasOwnProperty.call(data, "state") && Object.hasOwnProperty.call(data, "nonce")) {
        window.auth = {"state": data.state, "nonce": data.nonce};
    } else if (Array.isArray(data) && data[0][0] !== "e") {
        // Success with EntraID, works because of short circuit operators
        // Short circuit meaning that if the first cond fails, second not computed
        // because result already determined
        const idToken = data[0].slice(9);
        const returnState = data[1].slice(6);
        if (returnState.length == 6) {
            window.popup.close();
        }
        const jwtParts = idToken.split(".");
        window.parts = jwtParts;
        const header = JSON.parse(atob(jwtParts[0]));
        const body = JSON.parse(atob(jwtParts[1]));
        const sig = jwtParts[2];
        const time = Math.floor(Date.now() / 1000);
        if (
            returnState === window.auth.state &&
            body.aud === clientId &&
            body.nonce === window.auth.nonce &&
            body.iss === "https://login.microsoftonline.com/" + body.tid + "/v2.0" &&
            body.iat >= body.nbf && body.iat < body.exp && time > body.iat &&
            body.exp > time
        ) {
            // All parts of JWT body are good
            let fetchBody = {
                platform: "ms",
                platform_id: {
                    oid: body.oid,
                    tid: body.tid
                },
                email: body.email,
            };
            if (Object.hasOwnProperty.call(body, "preferred_username")) {
                fetchBody.username = body.preferred_username;
            }
            if (Object.hasOwnProperty.call(body, "name")) {
                fetchBody.name = body.name;
            }
            const data = await (await fetch("/api/users/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                "body": JSON.stringify(fetchBody)
            })).json();
            if (data.status) {
                document.getElementById("login").innerText = "LOGOUT";
                const saved = data.saved;
                if (saved != null) {
                    switch (window.location.pathname) {
                        case "/":
                            const savedE = document.querySelectorAll("#saved .item-list")[0];
                            savedE.innerHTML = "";
                            for (const item of saved) {
                                const card = createCard(item);
                                savedE.append(card);
                            }
                            break;
                    }
                }
                const recentlyViewed = data.recently_viewed;
                if (recentlyViewed != null) {
                    switch (window.location.pathname) {
                        case "/":
                            const recentlyViewedE = document.querySelectorAll("#recentView .item-list")[0];
                            recentlyViewedE.innerHTML = "";
                            for (const item of recentlyViewed) {
                                const card = createCard(item);
                                recentlyViewedE.append(card);
                            }
                            break;
                    }
                }
                const recentlySearched = data.recently_searched;
                if (recentlySearched != null) {
                    switch (window.location.pathname) {
                        case "/":
                            const recentlySearchedE = document.querySelectorAll("#recentSearch .item-list")[0];
                            recentlySearchedE.innerHTML = "";
                            for (const item of recentlySearched) {
                                const card = createCard(item);
                                recentlySearchedE.append(card);
                            }
                            break;
                    }
                }
                wrapCards()
            }
        } else {
            throw new Error("JWT Bad. Content: " + JSON.stringify(body))
        }
    } else {
        // An error happened in auth
        const code = data[0].slice(6);
        const desc = data[1].slice(18).replace("+", " ");
        alert("An error has occured during login. Code: " + code + ". Description: " + desc);
    }
}

function getIdToken(state, nonce) {
    const url = ("https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
    + "client_id=" + clientId + "&response_type=id_token&redirect_uri="
    + redirectUri + "&response=form_post&scope=" + scopes + "&state=" + state
    + "&prompt=none&nonce=" + nonce);
    window.addEventListener("message", onMessage);
    window.auth = {"state": state, "nonce": nonce};
    window.popup = window.open(url, "_blank");
    if (window.popup == null) {
        alert("Please enable popups to login, then try again")
    }
}

function toggleLogin(e) {
    if (e.target.innerText == "LOGIN") {
        let state = Math.floor(Math.random() * 1_000_000).toString();
        while (state.length < 6) {
            state = "0" + state;
        }
        state = state.slice(state.length - 6);
        const nonce = genString(32);
        const code = getIdToken(state, nonce);
    } else {
        fetch("/api/users/logout");
        const url = "https://login.microsoftonline.com/common/oauth2/v2.0/logout?post_logout_redirect_uri=" + encodeURIComponent(location.origin + "/browse");
        window.location = url;
    }
}

// Taken from https://stackoverflow.com/questions/1349404/generate-a-string-of-random-characters
function genString(length) {
    let result = "";
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    const charLength = chars.length;
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * charLength));
    }
    return result;
}

function init() {
    document.getElementById("login").addEventListener("click", toggleLogin);
}

if (document.readyState !== "loading") {
    init()
} else {
    document.addEventListener("DOMContentLoaded", init);
}
