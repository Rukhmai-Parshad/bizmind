/* BizMind: small progressive enhancements. Every page works without this file;
   it adds toasts that dismiss, the mobile menu, page search, a type filter,
   the selected-file name and button loading text. */
document.documentElement.classList.add("js");

document.addEventListener("DOMContentLoaded", function () {
    "use strict";

    var body = document.body;

    // 1. Toasts: dismiss button, auto-dismiss, 150ms fade.
    function closeToast(toast) {
        toast.classList.add("is-leaving");
        window.setTimeout(function () { toast.remove(); }, 160);
    }
    document.querySelectorAll(".toast").forEach(function (toast) {
        var button = toast.querySelector(".toast-close");
        if (button) { button.addEventListener("click", function () { closeToast(toast); }); }
        var delay = toast.classList.contains("toast-error") ? 10000 : 6000;
        window.setTimeout(function () { closeToast(toast); }, delay);
    });

    // 2. Mobile menu (off-canvas drawer).
    var menuButton = document.querySelector("[data-menu-button]");
    var scrim = document.querySelector("[data-scrim]");
    function setMenu(open) {
        body.classList.toggle("nav-open", open);
        if (menuButton) { menuButton.setAttribute("aria-expanded", open ? "true" : "false"); }
    }
    if (menuButton) { menuButton.addEventListener("click", function () { setMenu(!body.classList.contains("nav-open")); }); }
    if (scrim) { scrim.addEventListener("click", function () { setMenu(false); }); }
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && body.classList.contains("nav-open")) { setMenu(false); if (menuButton) { menuButton.focus(); } }
    });

    // 3. Page search and type filter. Both act on elements marked data-search-item.
    var items = Array.prototype.slice.call(document.querySelectorAll("[data-search-item]"));
    var searchForm = document.querySelector("[data-search]");
    var searchInput = searchForm ? searchForm.querySelector("input") : null;
    var counter = document.querySelector("[data-result-count]");
    var typeButtons = Array.prototype.slice.call(document.querySelectorAll("[data-type-filter]"));
    var activeType = "all";

    function applyFilters() {
        var query = searchInput ? searchInput.value.trim().toLowerCase() : "";
        var shown = 0;
        items.forEach(function (item) {
            var matchesText = !query || item.textContent.toLowerCase().indexOf(query) !== -1;
            var matchesType = activeType === "all" || item.getAttribute("data-type") === activeType;
            item.hidden = !(matchesText && matchesType);
            if (!item.hidden) { shown += 1; }
        });
        if (counter) {
            counter.hidden = !query && activeType === "all";
            counter.textContent = shown + " of " + items.length + " shown";
        }
    }

    if (searchForm) {
        if (items.length) {
            searchForm.hidden = false;
            searchInput.addEventListener("input", applyFilters);
            document.addEventListener("keydown", function (event) {
                var tag = event.target && event.target.tagName;
                var typing = tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (event.target && event.target.isContentEditable);
                if (event.key === "/" && !typing && !event.metaKey && !event.ctrlKey && !event.altKey) {
                    event.preventDefault();
                    searchInput.focus();
                }
            });
            searchInput.addEventListener("keydown", function (event) {
                if (event.key === "Escape") { searchInput.value = ""; applyFilters(); searchInput.blur(); }
            });
        }
    }
    typeButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            activeType = button.getAttribute("data-type-filter");
            typeButtons.forEach(function (other) { other.setAttribute("aria-pressed", other === button ? "true" : "false"); });
            applyFilters();
        });
    });

    // 4. Selected file name next to the file area.
    document.querySelectorAll('input[type="file"]').forEach(function (input) {
        var field = input.closest(".form-field");
        var label = field ? field.querySelector("[data-file-name]") : null;
        input.addEventListener("change", function () {
            var file = input.files && input.files[0];
            if (field) { field.classList.toggle("has-file", !!file); }
            if (label) { label.textContent = file ? "Selected: " + file.name : ""; }
        });
    });

    // 5. Loading text on submit buttons.
    document.querySelectorAll("form[data-loading-text]").forEach(function (form) {
        var button = form.querySelector('button[type="submit"]');
        if (!button) { return; }
        var original = button.textContent;
        form.addEventListener("submit", function () {
            button.disabled = true;
            button.textContent = form.dataset.loadingText;
        });
        // Coming back with the browser's Back button must not leave the button stuck.
        window.addEventListener("pageshow", function (event) {
            if (event.persisted) { button.disabled = false; button.textContent = original; }
        });
    });

    // 6. Upload page: show the required columns for the selected dataset type only.
    var typeField = document.getElementById("id_type");
    var schemas = document.querySelectorAll("[data-schema]");
    if (typeField && schemas.length) {
        var update = function () {
            schemas.forEach(function (block) { block.hidden = block.dataset.schema !== typeField.value; });
        };
        typeField.addEventListener("change", update);
        update();
    }
});
