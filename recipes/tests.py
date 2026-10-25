from django.test import TestCase, Client
from django.urls import reverse
from .models import SavedRecipe, RecipeVersion # Импортируем RecipeVersion
import json
import uuid

class RecipeEditorTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.recipe_data = {"title": "Тест", "ingredients": ["A"], "steps": ["B"]}
        self.recipe_json = "SMARTCHEF_JSON_V1\n" + json.dumps(self.recipe_data, ensure_ascii=False)
        
        self.test_token = str(uuid.uuid4())
        
        self.saved = SavedRecipe.objects.create(
            token=self.test_token,
            recipe=self.recipe_json,
            minutes=30,
            vegetarian=False,
            language="kk"
        )
        
        # Создаем версию, к которой будем откатываться
        self.version = RecipeVersion.objects.create(
            saved_recipe=self.saved,
            recipe=self.recipe_json
        )
        
        self.url = reverse("recipes:edit_saved_recipe", args=[self.saved.token])

    def test_rollback_functionality(self):
        # 1. Меняем основной рецепт на "Новый"
        new_recipe = {"title": "Новый", "ingredients": ["X"], "steps": ["Y"]}
        self.saved.recipe = "SMARTCHEF_JSON_V1\n" + json.dumps(new_recipe, ensure_ascii=False)
        self.saved.save()

        # 2. Отправляем POST-запрос на откат (передаем version_id!)
        response = self.client.post(self.url, {
            "action": "rollback",
            "version_id": self.version.id,
            "language": "kk"
        }, follow=True) # follow=True нужен, чтобы перейти по редиректу и увидеть сообщение

        # 3. Проверяем, что рецепт вернулся к исходному ("Тест")
        self.saved.refresh_from_db()
        self.assertIn("Тест", self.saved.recipe)
        
        # 4. Проверяем, что создалась новая версия (сохранение состояния до отката)
        self.assertEqual(RecipeVersion.objects.filter(saved_recipe=self.saved).count(), 2)
        
        # 5. Проверяем, что появилось сообщение об успехе
        self.assertContains(response, "Предыдущая версия восстановлена")