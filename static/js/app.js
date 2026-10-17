/* BizMind: two tiny progressive enhancements. Both pages work without this file. */
(function () {
    "use strict";

    // 1. Loading state: forms with data-loading-text disable the button and change its text.
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
            if (event.persisted) {
                button.disabled = false;
                button.textContent = original;
            }
        });
    });

    // 2. Upload page: show the required columns for the selected dataset type only.
    var typeField = document.getElementById("id_type");
    var schemas = document.querySelectorAll("[data-schema]");
    if (typeField && schemas.length) {
        var update = function () {
            schemas.forEach(function (block) {
                block.hidden = block.dataset.schema !== typeField.value;
            });
        };
        typeField.addEventListener("change", update);
        update();
    }
})();
