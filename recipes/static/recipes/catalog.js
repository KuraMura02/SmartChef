document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("catalog-search");

    const productCards = Array.from(
        document.querySelectorAll(".product-card")
    );

    const categoryButtons = Array.from(
        document.querySelectorAll(".category-button")
    );

    const selectedContainer =
        document.getElementById("catalog-selected");

    const countElement =
        document.getElementById("catalog-count");

    const clearButton =
        document.getElementById("catalog-clear");

    const noResults =
        document.getElementById("catalog-no-results");

    const emptyHint =
        document.getElementById("catalog-empty-hint");

    const catalogDataElement =
        document.getElementById("product-catalog-data");


    if (
        !searchInput ||
        !selectedContainer ||
        !countElement ||
        !clearButton
    ) {
        return;
    }


    let catalogData = {
        categories: [],
        products: [],
        language: "kk"
    };


    if (catalogDataElement) {
        try {
            catalogData = JSON.parse(
                document.getElementById(
                    "product-catalog-data"
                ).textContent
            );
        } catch (error) {
            catalogData = {
                categories: [],
                products: [],
                language: "kk"
            };
        }
    }


    const language =
        catalogData.language === "ru"
            ? "ru"
            : "kk";


    const productNames = {};


    catalogData.products.forEach((product) => {

        productNames[product.id] = {
            kk: String(product.kk || "").trim(),
            ru: String(product.ru || "").trim()
        };

    });


    let currentCategory = "all";


    function getCheckboxes() {

        return productCards
            .map((card) =>
                card.querySelector(
                    "input[name='selected_products']"
                )
            )
            .filter(Boolean);

    }


    function updateSelectedTags() {

        const checkboxes = getCheckboxes();

        const selected =
            checkboxes.filter(
                (checkbox) => checkbox.checked
            );


        countElement.textContent =
            String(selected.length);


        selectedContainer.textContent = "";


        if (selected.length === 0) {

            const hint =
                document.createElement("span");

            hint.className =
                "selection-hint";

            hint.textContent =
                language === "kk"
                    ? "Өнімдерді таңдаңыз."
                    : "Выберите продукты.";

            selectedContainer.appendChild(hint);


            if (emptyHint) {
                emptyHint.hidden = false;
            }

            return;
        }


        if (emptyHint) {
            emptyHint.hidden = true;
        }


        selected.forEach((checkbox) => {

            const productId =
                checkbox.value;

            const names =
                productNames[productId];


            const tag =
                document.createElement("span");

            tag.className =
                "selected-tag";


            const text =
                document.createElement("span");

            text.textContent =
                names
                    ? (
                        language === "kk"
                            ? names.kk
                            : names.ru
                    )
                    : productId;


            const removeButton =
                document.createElement("button");

            removeButton.type = "button";

            removeButton.className =
                "tag-remove";

            removeButton.setAttribute(
                "aria-label",
                language === "kk"
                    ? "Өнімді алып тастау"
                    : "Удалить продукт"
            );

            removeButton.textContent = "×";


            removeButton.addEventListener(
                "click",
                () => {

                    checkbox.checked = false;

                    updateSelectedTags();

                }
            );


            tag.appendChild(text);

            tag.appendChild(removeButton);

            selectedContainer.appendChild(tag);

        });

    }


    function applyFilter() {

        const query =
            searchInput.value
                .trim()
                .toLowerCase();

        let visibleCount = 0;


        productCards.forEach((card) => {

            const productId =
                card.dataset.productId || "";

            const productCategory =
                card.dataset.category || "";


            const names =
                productNames[productId] || {
                    kk: "",
                    ru: ""
                };


            const kkName =
                names.kk
                    .trim()
                    .toLowerCase();

            const ruName =
                names.ru
                    .trim()
                    .toLowerCase();


            const matchesSearch =
                query === "" ||
                kkName.includes(query) ||
                ruName.includes(query);


            const matchesCategory =
                currentCategory === "all" ||
                productCategory === currentCategory;


            const shouldShow =
                matchesSearch &&
                matchesCategory;


            card.hidden =
                !shouldShow;


            if (shouldShow) {
                visibleCount += 1;
            }

        });


        if (noResults) {
            noResults.hidden =
                visibleCount !== 0;
        }

    }


    categoryButtons.forEach((button) => {

        button.addEventListener(
            "click",
            () => {

                currentCategory =
                    button.dataset.category ||
                    "all";


                categoryButtons.forEach((item) => {

                    const active =
                        item === button;


                    item.classList.toggle(
                        "active",
                        active
                    );


                    item.setAttribute(
                        "aria-pressed",
                        active
                            ? "true"
                            : "false"
                    );

                });


                applyFilter();

            }
        );

    });


    searchInput.addEventListener(
        "input",
        () => {
            applyFilter();
        }
    );


    getCheckboxes().forEach((checkbox) => {

        checkbox.addEventListener(
            "change",
            () => {
                updateSelectedTags();
            }
        );

    });


    clearButton.addEventListener(
        "click",
        () => {

            getCheckboxes().forEach(
                (checkbox) => {
                    checkbox.checked = false;
                }
            );

            updateSelectedTags();

        }
    );


    updateSelectedTags();

    applyFilter();

});
