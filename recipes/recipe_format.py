
import json

PREFIX = "SMARTCHEF_JSON_V1"

MAX_RESPONSE_LENGTH = 30000
MAX_TITLE_LENGTH = 120
MAX_INGREDIENTS = 24
MAX_INGREDIENT_LENGTH = 200
MAX_STEPS = 12
MAX_STEP_LENGTH = 1200

EXPECTED_KEYS = {"title", "ingredients", "steps"}


class RecipeFormatError(ValueError):
    """Қате рецепт пішіміне арналған ерекшелік."""


def _reject_duplicate_keys(pairs):
    """JSON ішіндегі қайталанатын кілттерді қабылдамау."""
    result = {}

    for key, value in pairs:
        if key in result:
            raise RecipeFormatError(
                f"JSON ішінде қайталанған кілт бар: {key}"
            )
        result[key] = value

    return result


def _reject_constant(value):
    """NaN және Infinity сияқты JSON-ға жат мәндерді қабылдамау."""
    raise RecipeFormatError(f"Рұқсат етілмеген JSON мәні: {value}")


def validate_recipe(data):
    """Рецепт құрылымын және барлық өрістерді тексеру."""
    if not isinstance(data, dict):
        raise RecipeFormatError("Рецепт JSON объектісі болуы керек.")

    if set(data.keys()) != EXPECTED_KEYS:
        raise RecipeFormatError(
            "Рецепт тек title, ingredients және steps өрістерін қамтуы керек."
        )

    title = data["title"]
    ingredients = data["ingredients"]
    steps = data["steps"]

    if not isinstance(title, str):
        raise RecipeFormatError("title мәтін болуы керек.")

    if not 1 <= len(title.strip()) <= MAX_TITLE_LENGTH:
        raise RecipeFormatError(
            "title ұзындығы 1–120 таңба аралығында болуы керек."
        )

    if not isinstance(ingredients, list):
        raise RecipeFormatError("ingredients тізім болуы керек.")

    if not 1 <= len(ingredients) <= MAX_INGREDIENTS:
        raise RecipeFormatError(
            "ingredients тізімінде 1–24 өнім болуы керек."
        )

    for index, ingredient in enumerate(ingredients, start=1):
        if not isinstance(ingredient, str):
            raise RecipeFormatError(
                f"{index}-ингредиент мәтін болуы керек."
            )

        if not 1 <= len(ingredient.strip()) <= MAX_INGREDIENT_LENGTH:
            raise RecipeFormatError(
                f"{index}-ингредиент бос болмауы және 200 таңбадан аспауы керек."
            )

    if not isinstance(steps, list):
        raise RecipeFormatError("steps тізім болуы керек.")

    if not 1 <= len(steps) <= MAX_STEPS:
        raise RecipeFormatError(
            "steps тізімінде 1–12 қадам болуы керек."
        )

    for index, step in enumerate(steps, start=1):
        if not isinstance(step, str):
            raise RecipeFormatError(
                f"{index}-қадам мәтін болуы керек."
            )

        if not 1 <= len(step.strip()) <= MAX_STEP_LENGTH:
            raise RecipeFormatError(
                f"{index}-қадам бос болмауы және 1200 таңбадан аспауы керек."
            )

    return {
        "title": title.strip(),
        "ingredients": [item.strip() for item in ingredients],
        "steps": [step.strip() for step in steps],
    }


def parse_recipe_json(raw_text):
    """Gemini жауабын тексеріп, құрылымды рецепт ретінде қайтару."""
    if not isinstance(raw_text, str):
        raise RecipeFormatError("Рецепт жауабы мәтін болуы керек.")

    if not raw_text.strip():
        raise RecipeFormatError("Рецепт жауабы бос.")

    if len(raw_text) > MAX_RESPONSE_LENGTH:
        raise RecipeFormatError("Рецепт жауабы 30000 таңбадан асып кетті.")

    try:
        data = json.loads(
            raw_text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except RecipeFormatError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise RecipeFormatError(
            "Gemini дұрыс JSON қайтармады."
        ) from exc

    return validate_recipe(data)


def encode_recipe(data):
    """Тексерілген рецептті ескі recipe өрісіне сақтауға дайындау."""
    validated = validate_recipe(data)
    json_text = json.dumps(
        validated,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    result = f"{PREFIX}\n{json_text}"

    if len(result) > MAX_RESPONSE_LENGTH + len(PREFIX) + 1:
        raise RecipeFormatError("Сақталатын рецепт тым ұзын.")

    return result


def decode_recipe(recipe_text):
    """Құрылымды рецептті оқу; ескі мәтінді өзгертпей қайтару."""
    if not isinstance(recipe_text, str):
        return None

    prefix = PREFIX + "\n"

    if not recipe_text.startswith(prefix):
        return None

    raw_json = recipe_text[len(prefix):]

    if len(raw_json) > MAX_RESPONSE_LENGTH:
        raise RecipeFormatError("Сақталған рецепт тым ұзын.")

    try:
        data = json.loads(
            raw_json,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except RecipeFormatError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise RecipeFormatError(
            "Сақталған рецепттің JSON форматы қате."
        ) from exc

    return validate_recipe(data)
