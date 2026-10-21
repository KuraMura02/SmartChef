
from django.urls import path

from . import views
from .recipe_editor import edit_saved_recipe


app_name = "recipes"


urlpatterns = [
    path("", views.index, name="index"),
    path("save/", views.save_recipe, name="save_recipe"),
    path("saved/", views.saved_recipes, name="saved_recipes"),
    path(
        "saved/<uuid:token>/edit/",
        edit_saved_recipe,
        name="edit_saved_recipe",
    ),
    path("cooking/", views.cooking, name="cooking"),
]
