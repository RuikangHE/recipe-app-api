from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Ingredient, Recipe
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')


def recipe_detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_sample_tag(user, name='Main course'):
    """Helper function to create a sample Tag"""
    return Tag.objects.create(user=user, name=name)


def create_sample_ingredient(user, name='Cinnamon'):
    """Helper function to create a sample Ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def create_sample_recipe(user, **params):
    default = {
        'title': 'Sample Recipe',
        'time_minutes': 10,
        'price': 5.00,
    }
    default.update(params)

    return Recipe.objects.create(user=user, **default)


class PublicRecipeApiTest(TestCase):
    """Test the publically available recipe API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTest(TestCase):
    """Test the authenticated users recipe API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            email='sample@gmail.com',
            password='Testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        """Test retriving recipes"""
        create_sample_recipe(user=self.user)
        create_sample_recipe(user=self.user)
        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        another_user = get_user_model().objects.create_user(
            email='another@gmail.com',
            password='anotherpass123'
        )
        create_sample_recipe(user=another_user)
        create_sample_recipe(user=self.user)
        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_detail_view(self):
        """Test viewing a recipe's detail"""
        recipe = create_sample_recipe(user=self.user)
        recipe.tags.add(create_sample_tag(user=self.user))
        recipe.ingredients.add(create_sample_ingredient(user=self.user))
        url = recipe_detail_url(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating a basic recipe without tags or ingredients"""
        payload = {
            'title': 'Fruit Cake',
            'time_minutes': 30,
            'price': 10.00
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""
        tag1 = create_sample_tag(user=self.user, name='Vegan')
        tag2 = create_sample_tag(user=self.user, name='Dessert')
        payload = {
            'title': 'Samle Recipe',
            'time_minutes': 10,
            'price': 3.00,
            'tags': [tag1.id, tag2.id]
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()

        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with ingredients"""
        ingr1 = create_sample_ingredient(user=self.user, name='Salt')
        ingr2 = create_sample_ingredient(user=self.user, name='Sugar')
        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 10,
            'price': 9.99,
            'ingredients': [ingr1.id, ingr2.id]
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingr1, ingredients)
        self.assertIn(ingr2, ingredients)
