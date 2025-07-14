const clientId = "21b089d7-aa3e-478f-a992-9aa757adc73f";
const redirectUri = encodeURIComponent(location.origin + "/api/oidc/redirect");
const scopes = encodeURIComponent(["openid", "email", "profile"].join(" "));

function onMessage(e) {
    const data = e.data;
    window.data = e.data;
    if (data[0][0] !== "e") {
        // Success with EntraID
        const idToken = data[0].slice(9);
        const returnState = data[1].slice(6);
        if (returnState.length == 6) {
            window.popup.postMessage("close");
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
            fetch("/api/users/send", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                "body": JSON.stringify({
                    platform: "ms",
                    platform_id: {
                        oid: body.oid,
                        tid: body.tid
                    }
                })
            });
        }
    } else {
        // An error happened in auth
        const code = data[0].slice(6);
        if (code === "login_required" || code === "interaction_required") {
            window.popup.postMessage("close");
            login(undefined, "login")
        } else {
            const desc = data[1].slice(18).replace("+", " ");
            alert("An error has occured during login. Code: " + code + ". Description: " + desc);
        }
    }
}

function getIdToken(state, nonce, prompt) {
    const url = ("https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
    + "client_id=" + clientId + "&response_type=id_token&redirect_uri="
    + redirectUri + "&response=form_post&scope=" + scopes + "&state=" + state
    + "&prompt=" + prompt + "&nonce=" + nonce);
    window.addEventListener("message", onMessage);
    window.auth = {"state": state, "nonce": nonce};
    window.popup = window.open(url, "_blank");
    if (window.popup == null) {
        alert("Please enable popups to login, then try again")
    }
}

function login(e, prompt="none") {
    let state = Math.floor(Math.random() * 1_000_000).toString();
    while (state.length < 6) {
        state = "0" + state;
    }
    state = state.slice(state.length - 6);
    const nonce = genString(32);
    const code = getIdToken(state, nonce, prompt);
}


// Taken from https://stackoverflow.com/questions/1349404/generate-a-string-of-random-characters
function genString(length) {
    let result = "";
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    const charLength = chars.length;
    for (let i = 0; i < charLength; i++) {
        result += chars.charAt(Math.floor(Math.random() * charLength));
    }
    return result;
}

function init() {
    document.getElementById("login").addEventListener("click", login);
}

if (document.readyState !== "loading") {
    init()
} else {
    document.addEventListener("DOMContentLoaded", init);
}