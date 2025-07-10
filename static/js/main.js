/* 
 * Stumbled upon this recently. I've done some of its suggestions before, but its pretty neat
 * https://youmightnotneedjquery.com/
 */

if (!window.app) {
    window.app = {};
}

window.app.toggleSave = function(e) {
    let target = e.target;
    if (target.innerHTML.length === 0) {
        target = target.parentElement;
    }
    for (let child of target.children) {
        child.classList.toggle("hidden");
    }
}

window.app.init = function() {
    document.querySelectorAll(".save-icons").forEach((e) => {
        e.addEventListener("click", window.app.toggleSave);
    });
}

if (document.readyState !== "loading") {
    window.app.init()
} else {
    document.addEventListener("DOMContentLoaded", window.app.init);
}