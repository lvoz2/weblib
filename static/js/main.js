function toggleSave(e) {
    let target = e.target;
    if (target.innerHTML.length === 0) {
        target = target.parentElement;
    }
    for (let child of target.children) {
        child.classList.toggle("hidden");
    }
}

function init() {
    document.querySelectorAll(".save-icons").forEach((e) => {
        e.addEventListener("click", toggleSave);
    });
}

if (document.readyState !== "loading") {
    init()
} else {
    document.addEventListener("DOMContentLoaded", init);
}