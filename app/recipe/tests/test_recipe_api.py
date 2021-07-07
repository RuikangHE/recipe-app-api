from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Ingredient, Recipe
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

import os
import tempfile

from PIL import Image


RECIPES_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch"""
        recipe = create_sample_recipe(user=self.user)
        recipe.tags.add(create_sample_tag(user=self.user))
        new_tag = create_sample_tag(user=self.user, name='Curry')
        payload = {
            'title': 'Chicken Skewers',
            'tags': [new_tag.id]
        }
        url = recipe_detail_url(recipe.id)
        self.client.patch(url, payload)
        recipe.refresh_from_db()
        tags = recipe.tags.all()

        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(tags.count(), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """Test updating a recipe with put"""
        recipe = create_sample_recipe(user=self.user)
        tag = create_sample_tag(user=self.user)
        payload = {
            'title': 'Lamb Skewers',
            'time_minutes': 5,
            'price': 2.00,
            'tags': [tag.id]
        }
        url = recipe_detail_url(recipe.id)
        self.client.put(url, payload)
        recipe.refresh_from_db()
        tags = recipe.tags.all()

        for key in payload.keys():
            if key == 'tags':
                continue
            self.assertEqual(payload[key], getattr(recipe, key))
        self.assertEqual(tags.count(), 1)
        self.assertIn(tag, tags)


class RecipeImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            email='sample@user.com',
            password='testpass'
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_recipe_image(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            payload = {'image': ntf}
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_invalid_recipe_image(self):
        url = image_upload_url(self.recipe.id)
        payload = {'image': 'invalidimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class RecipeFilterTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            email='sample@user.com',
            password='testpass'
        )
        self.client.force_authenticate(self.user)
        self.recipe1 = create_sample_recipe(user=self.user, title='recipe 1')
        self.recipe2 = create_sample_recipe(user=self.user, title='recipe 2')
        self.basic_recipe = create_sample_recipe(
            user=self.user,
            title='recipe 3'
        )

    def test_filter_recipe_by_tags(self):
        tag1 = create_sample_tag(user=self.user, name='tag 1')
        tag2 = create_sample_tag(user=self.user, name='tag 2')
        self.recipe1.tags.add(tag1)
        self.recipe2.tags.add(tag2)
        payload = {'tags': f'{tag1.id},{tag2.id}'}
        res = self.client.get(RECIPES_URL, payload)
        serializer1 = RecipeSerializer(self.recipe1)
        serializer2 = RecipeSerializer(self.recipe2)
        serializer3 = RecipeSerializer(self.basic_recipe)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        ingr1 = create_sample_ingredient(user=self.user, name='ingr 1')
        ingr2 = create_sample_ingredient(user=self.user, name='ingr 2')
        self.recipe1.ingredients.add(ingr1)
        self.recipe2.ingredients.add(ingr2)
        payload = {'ingredients': f'{ingr1.id},{ingr2.id}'}
        res = self.client.get(RECIPES_URL, payload)
        serializer1 = RecipeSerializer(self.recipe1)
        serializer2 = RecipeSerializer(self.recipe2)
        serializer3 = RecipeSerializer(self.basic_recipe)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)
