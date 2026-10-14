
document.addEventListener("DOMContentLoaded", () => {
    const app = document.getElementById("cooking-app");
    const dataElement = document.getElementById("cooking-recipe-data");

    if (!app || !dataElement) {
        return;
    }

    let recipe;

    try {
        recipe = JSON.parse(dataElement.textContent);
    } catch {
        return;
    }

    if (
        !recipe ||
        !Array.isArray(recipe.steps) ||
        recipe.steps.length < 1
    ) {
        return;
    }

    const language = app.dataset.language === "ru" ? "ru" : "kk";
    const steps = recipe.steps;

    let currentStep = 0;
    const completedSteps = new Set();

    const currentNumber = document.getElementById("current-step-number");
    const completedNumber = document.getElementById("completed-step-number");
    const totalNumber = document.getElementById("total-step-number");
    const stepHeading = document.getElementById("step-heading");
    const stepText = document.getElementById("step-text");
    const progressTrack = document.getElementById("cooking-progress-track");
    const progressFill = document.getElementById("cooking-progress-fill");
    const previousButton = document.getElementById("previous-step");
    const confirmButton = document.getElementById("confirm-step");
    const restartButton = document.getElementById("restart-cooking");
    const stepPanel = document.getElementById("cooking-step-panel");
    const completePanel = document.getElementById("cooking-complete-panel");
    const actions = document.getElementById("cooking-actions");
    const status = document.getElementById("cooking-status");

    totalNumber.textContent = String(steps.length);

    function render() {
        const finished = completedSteps.size === steps.length;

        currentNumber.textContent = String(
            Math.min(currentStep + 1, steps.length)
        );
        completedNumber.textContent = String(completedSteps.size);

        progressTrack.setAttribute("aria-valuemax", String(steps.length));
        progressTrack.setAttribute("aria-valuenow", String(completedSteps.size));

        progressFill.style.width =
            `${(completedSteps.size / steps.length) * 100}%`;

        stepPanel.hidden = finished;
        completePanel.hidden = !finished;
        actions.hidden = finished;

        if (finished) {
            status.textContent = language === "ru"
                ? "Все шаги выполнены."
                : "Барлық қадам орындалды.";
            return;
        }

        stepHeading.textContent = language === "ru"
            ? `Шаг ${currentStep + 1}`
            : `Қадам ${currentStep + 1}`;

        stepText.textContent = steps[currentStep];

        previousButton.disabled = currentStep === 0;

        const alreadyCompleted = completedSteps.has(currentStep);

        confirmButton.disabled = alreadyCompleted;
        confirmButton.textContent = alreadyCompleted
            ? (language === "ru" ? "Шаг выполнен" : "Қадам орындалды")
            : (language === "ru" ? "Подтвердить шаг" : "Қадамды растау");

        status.textContent = alreadyCompleted
            ? (language === "ru"
                ? "Этот шаг уже отмечен как выполненный."
                : "Бұл қадам орындалды деп белгіленген.")
            : "";
    }

    previousButton.addEventListener("click", () => {
        if (currentStep > 0) {
            currentStep -= 1;
            render();
        }
    });

    confirmButton.addEventListener("click", () => {
        if (completedSteps.has(currentStep)) {
            return;
        }

        completedSteps.add(currentStep);

        if (completedSteps.size === steps.length) {
            render();
            return;
        }

        if (currentStep < steps.length - 1) {
            currentStep += 1;
        }

        render();
    });

    restartButton.addEventListener("click", () => {
        currentStep = 0;
        completedSteps.clear();
        render();
    });

    render();
});
