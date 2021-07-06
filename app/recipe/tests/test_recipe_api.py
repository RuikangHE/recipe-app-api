from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from recipe.serializers import RecipeSerializer


RECIPE_URLS = reverse('recipe:recipe-list')


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
        res = self.client.get(RECIPE_URLS)

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
        res = self.client.get(RECIPE_URLS)
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
        res = self.client.get(RECIPE_URLS)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
