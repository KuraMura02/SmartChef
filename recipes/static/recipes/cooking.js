(function () {
    function init() {
        const app = document.getElementById("cooking-app");
        const dataElement = document.getElementById("cooking-recipe-data");

        if (!app || !dataElement) {
            console.error("SmartChef: не найден контейнер #cooking-app или данные #cooking-recipe-data.");
            return;
        }

        let recipe;
        try {
            recipe = JSON.parse(dataElement.textContent);
        } catch (error) {
            console.error("SmartChef: не удалось прочитать JSON рецепта.", error);
            return;
        }

        if (!recipe || !Array.isArray(recipe.steps) || recipe.steps.length === 0) {
            console.error("SmartChef: шаги рецепта пусты или неверного формата.", recipe);
            return;
        }

        const language = app.dataset.language === "ru" ? "ru" : "kk";
        const steps = recipe.steps;

        let currentStep = 0;
        const completedSteps = new Set();

        const el = (id) => document.getElementById(id);
        const currentNumber   = el("current-step-number");
        const completedNumber = el("completed-step-number");
        const totalNumber     = el("total-step-number");
        const stepHeading     = el("step-heading");
        const stepText        = el("step-text");
        const progressTrack   = el("cooking-progress-track");
        const progressFill    = el("cooking-progress-fill");
        const previousButton  = el("previous-step");
        const confirmButton   = el("confirm-step");
        const restartButton   = el("restart-cooking");
        const stepPanel       = el("cooking-step-panel");
        const completePanel   = el("cooking-complete-panel");
        const actions         = el("cooking-actions");
        const status          = el("cooking-status");

        const required = {
            currentNumber, completedNumber, totalNumber, stepHeading, stepText,
            progressTrack, progressFill, previousButton, confirmButton,
            restartButton, stepPanel, completePanel, actions, status
        };

        const missing = Object.entries(required)
            .filter(([, node]) => !node)
            .map(([name]) => name);

        if (missing.length) {
            console.error("SmartChef: не найдены элементы HTML:", missing.join(", "));
            return;
        }

        totalNumber.textContent = String(steps.length);

        function render() {
            const finished = completedSteps.size === steps.length;

            currentNumber.textContent = String(finished ? steps.length : currentStep + 1);
            completedNumber.textContent = String(completedSteps.size);

            progressTrack.setAttribute("aria-valuemax", String(steps.length));
            progressTrack.setAttribute("aria-valuenow", String(completedSteps.size));
            progressFill.style.width = `${(completedSteps.size / steps.length) * 100}%`;

            stepPanel.hidden = finished;
            completePanel.hidden = !finished;
            actions.hidden = finished;

            if (finished) {
                status.textContent = language === "ru"
                    ? "Все шаги выполнены."
                    : "Барлық қадам орындалды!";
                return;
            }

            stepHeading.textContent = language === "ru"
                ? `Шаг ${currentStep + 1}`
                : `Қадам ${currentStep + 1}`;
            stepText.textContent = steps[currentStep];
            previousButton.disabled = currentStep === 0;

            const alreadyCompleted = completedSteps.has(currentStep);
            confirmButton.disabled = false;
            confirmButton.textContent = alreadyCompleted
                ? (language === "ru" ? "Шаг выполнен ✓" : "Қадам орындалды ✓")
                : (language === "ru" ? "Подтвердить шаг" : "Қадамды растау");

            status.textContent = alreadyCompleted
                ? (language === "ru" ? "Этот шаг уже выполнен." : "Бұл қадам орындалған.")
                : "";
        }

        // Делегирование: работает даже если кнопки перерисуют/заменят
        app.addEventListener("click", (event) => {
            const button = event.target.closest("button");
            if (!button) return;

            switch (button.id) {
                case "confirm-step": {
                    completedSteps.add(currentStep);
                    if (completedSteps.size < steps.length) {
                        currentStep = Math.min(currentStep + 1, steps.length - 1);
                    }
                    render();
                    break;
                }
                case "previous-step": {
                    if (currentStep > 0) {
                        currentStep--;
                        render();
                    }
                    break;
                }
                case "restart-cooking": {
                    currentStep = 0;
                    completedSteps.clear();
                    render();
                    break;
                }
            }
        });

        render();
        console.info("SmartChef: режим приготовления инициализирован.");
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();