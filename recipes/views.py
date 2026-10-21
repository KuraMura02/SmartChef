import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .catalog import CATEGORIES, PRODUCTS, build_products
from .models import SavedRecipe
from .recipe_format import (
    RecipeFormatError,
    decode_recipe,
    encode_recipe,
    parse_recipe_json,
)


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

ALLOWED_LANGUAGES = {"kk", "ru"}
ALLOWED_TIMES = {"15", "30", "60"}

def call_gemini(prompt, api_key=None, model=None):
    """Существующий серверный способ обращения к Gemini."""
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    model = model or os.environ.get(
        "GEMINI_MODEL",
        "gemini-3.8-flash",
    )

    if not api_key:
        raise ValueError("GEMINI_API_KEY не найден.")

    client = genai.Client(api_key=api_key)

    interaction = client.interactions.create(
        model=model,
        input=prompt,
    )

    return interaction.output_text or ""

def format_recipe_for_display(data, language):
    """Құрылымды рецептті пайдаланушыға оқуға ыңғайлы мәтінге айналдыру."""
    if language == "ru":
        lines = [
            data["title"],
            "",
            "Ингредиенты:",
        ]
        lines.extend(f"• {item}" for item in data["ingredients"])
        lines.extend(["", "Приготовление:"])
        lines.extend(
            f"{index}. {step}"
            for index, step in enumerate(data["steps"], start=1)
        )
    else:
        lines = [
            data["title"],
            "",
            "Құрамы:",
        ]
        lines.extend(f"• {item}" for item in data["ingredients"])
        lines.extend(["", "Дайындау жолы:"])
        lines.extend(
            f"{index}. {step}"
            for index, step in enumerate(data["steps"], start=1)
        )

    return "\n".join(lines)


def index(request):
    language = request.GET.get("language", "kk")

    if language not in ALLOWED_LANGUAGES:
        language = "kk"

    products = ""
    minutes = "30"
    vegetarian = False
    recipe = ""
    recipe_is_structured = False
    error = ""
    can_save = False
    selected_products = []

    if request.method == "POST":
        action = request.POST.get("action", "generate")

        if action == "language":
            new_language = (
                request.GET.get("language")
                or request.POST.get("target_language")
                or request.POST.get("language", "kk")
            )

            language = (
                new_language
                if new_language in ALLOWED_LANGUAGES
                else "kk"
            )

            raw_ids = list(
                dict.fromkeys(
                    request.POST.getlist("selected_products")
                )
            )

            lookup = {product["id"]: product for product in PRODUCTS}

            selected_products = [
                product_id
                for product_id in raw_ids
                if product_id in lookup
            ]

            products = request.POST.get("products", "")

            minutes = request.POST.get("minutes", "30")
            if minutes not in ALLOWED_TIMES:
                minutes = "30"

            vegetarian = request.POST.get("vegetarian") == "on"

            # Переключение языка не вызывает Gemini.
            # Черновик очищается согласно требованиям задания.
            request.session.pop("smartchef_draft", None)

        elif action == "generate":
            language = request.POST.get("language", "kk")

            if language not in ALLOWED_LANGUAGES:
                language = "kk"

            raw_ids = list(
                dict.fromkeys(
                    request.POST.getlist("selected_products")
                )
            )

            products = request.POST.get("products", "")

            minutes = request.POST.get("minutes", "30")
            if minutes not in ALLOWED_TIMES:
                minutes = "30"

            vegetarian = request.POST.get("vegetarian") == "on"

            # Новый запрос начинает новый черновик.
            request.session.pop("smartchef_draft", None)

            try:
                selected_products, combined = build_products(
                    raw_ids,
                    products,
                    language,
                )

                api_key = os.environ.get("GEMINI_API_KEY")
                model = os.environ.get(
                    "GEMINI_MODEL",
                    "gemini-3.8-flash",
                )

                if not api_key:
                    raise ValueError(
                        "GEMINI_API_KEY табылмады."
                        if language == "kk"
                        else "GEMINI_API_KEY не найден."
                    )

                if language == "kk":
                    language_instruction = (
                        "Барлық мәтінді қазақ тілінде жаз."
                    )
                    vegetarian_instruction = (
                        "Тағам етсіз болуы керек."
                        if vegetarian
                        else "Етсіз тағам міндетті емес."
                    )
                else:
                    language_instruction = (
                        "Весь текст напиши на русском языке."
                    )
                    vegetarian_instruction = (
                        "Блюдо должно быть без мяса."
                        if vegetarian
                        else "Вегетарианское блюдо не обязательно."
                    )

                prompt = f"""
Ты — кулинарный помощник SmartChef.

Создай один простой и понятный рецепт из перечисленных продуктов.
Продукты пользователя: {combined}
Максимальное время приготовления: {minutes} минут.
{vegetarian_instruction}
{language_instruction}

Верни ТОЛЬКО корректный JSON, без Markdown, без блока ``` и без текста до или после JSON.

Строгая структура:
{{
  "title": "Название рецепта",
  "ingredients": ["Ингредиент 1", "Ингредиент 2"],
  "steps": ["Первый шаг", "Второй шаг"]
}}

Требования:
- Только три ключа: title, ingredients, steps.
- title: непустая строка длиной от 1 до 120 символов.
- ingredients: массив из 1–24 непустых строк, каждая до 200 символов.
- steps: массив из 1–12 непустых строк, каждая до 1200 символов.
- Используй только реальные, выполнимые действия.
- Не выдумывай шаги, которых нет в рецепте.
- Учитывай указанное время и продукты.
- Не добавляй комментарии и дополнительные ключи.
""".strip()

                raw_response = call_gemini(
    prompt,
    api_key=api_key,
    model=model,
)

                if not raw_response.strip():
                    raise RecipeFormatError(
                        "Gemini бос жауап қайтарды."
                        if language == "kk"
                        else "Gemini вернул пустой ответ."
                    )

                # Проверяем JSON до сохранения.
                recipe_data = parse_recipe_json(raw_response)

                # Сохраняем структуру в прежнее поле recipe.
                stored_recipe = encode_recipe(recipe_data)

                recipe = format_recipe_for_display(
                    recipe_data,
                    language,
                )

                recipe_is_structured = True
                can_save = True

                draft = {
                    "token": str(uuid.uuid4()),
                    "products": combined,
                    "recipe": stored_recipe,
                    "language": language,
                    "minutes": int(minutes),
                    "vegetarian": bool(vegetarian),
                }

                request.session["smartchef_draft"] = draft

            except RecipeFormatError as exc:
                error = (
                    f"Gemini жауабының форматы қате: {exc}"
                    if language == "kk"
                    else f"Неверный формат ответа Gemini: {exc}"
                )

            except ValueError as exc:
                error = str(exc)

            except Exception:
                error = (
                    "Рецепт жасау кезінде қате пайда болды. "
                    "API кілтін және Gemini қолжетімділігін тексер."
                    if language == "kk"
                    else
                    "При создании рецепта произошла ошибка. "
                    "Проверь API-ключ и доступность Gemini."
                )

    context = {
        "language": language,
        "products": products,
        "minutes": minutes,
        "vegetarian": vegetarian,
        "recipe": recipe,
        "recipe_is_structured": recipe_is_structured,
        "cooking_url": reverse("recipes:cooking"),
        "error": error,
        "can_save": can_save,
        "categories": CATEGORIES,
        "catalog_products": PRODUCTS,
        "selected_products": selected_products,
        "catalog_data": {
            "categories": CATEGORIES,
            "products": PRODUCTS,
            "language": language,
        },
    }

    return render(request, "recipes/index.html", context)


@require_POST
def save_recipe(request):
    draft = request.session.get("smartchef_draft")

    if not draft:
        language = request.POST.get("language", "kk")

        if language not in ALLOWED_LANGUAGES:
            language = "kk"

        return redirect(f"/?language={language}")

    SavedRecipe.objects.get_or_create(
        token=draft["token"],
        defaults={
            "products": draft["products"],
            "recipe": draft["recipe"],
            "language": draft["language"],
            "minutes": draft["minutes"],
            "vegetarian": draft["vegetarian"],
        },
    )

    return redirect(
        f"{reverse('recipes:saved_recipes')}?language={draft['language']}"
    )


def saved_recipes(request):
    language = request.GET.get("language", "kk")

    if language not in ALLOWED_LANGUAGES:
        language = "kk"

    recipes = SavedRecipe.objects.all()

    # Разбираем сохранённый JSON каждого рецепта
    for saved in recipes:
        saved.display_title = "Рецепт"
        saved.display_ingredients = []
        saved.display_steps = []

        raw_recipe = saved.recipe or ""

        try:
            if raw_recipe.startswith("SMARTCHEF_JSON_V1"):
                raw_recipe = raw_recipe.split("\n", 1)[1]

            data = json.loads(raw_recipe)

            saved.display_title = data.get("title") or "Рецепт"
            saved.display_ingredients = data.get("ingredients", [])
            saved.display_steps = data.get("steps", [])

        except (ValueError, IndexError, TypeError, AttributeError):
            # Если старый рецепт не в формате JSON,
            # показываем его текст как есть
            saved.display_steps = [raw_recipe] if raw_recipe else []

    return render(
        request,
        "recipes/saved.html",
        {
            "language": language,
            "recipes": recipes,
        },
    )


def cooking(request):
    """Соңғы жаңа құрылымды рецепт үшін дайындау режимін ашу."""
    language = request.GET.get("language", "kk")

    if language not in ALLOWED_LANGUAGES:
        language = "kk"

    draft = request.session.get("smartchef_draft")

    if not draft:
        return redirect(f"/?language={language}")

    try:
        recipe_data = decode_recipe(draft.get("recipe", ""))
    except RecipeFormatError:
        recipe_data = None

    # Ескі қарапайым мәтіндік рецепттерді режимге жібермейміз.
    if recipe_data is None:
        return redirect(f"/?language={draft.get('language', language)}")

    language = draft.get("language", language)

    if language not in ALLOWED_LANGUAGES:
        language = "kk"

    return render(
        request,
        "recipes/cooking.html",
        {
            "language": language,
            "recipe_data": recipe_data,
            "recipe_url": reverse("recipes:index"),
            "demo_fixture": False,
        },
    )
