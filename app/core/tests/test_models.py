from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models
from unittest.mock import patch
import os


def sample_user(email='sample@gmail.com', password='sample123'):
    """Create a sample user"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    password = 'Testpass123'
    email = 'sample@email.com'

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful"""
        user = get_user_model().objects.create_user(
            email=self.email,
            password=self.password
        )

        self.assertEqual(user.email, self.email)
        self.assertTrue(user.check_password(self.password))

    def test_user_email_normalized(self):
        """Test the newly created user's email is normalized"""
        email_identifier = 'sample'
        email_domain = 'GMAIL.com'
        email = f'{email_identifier}@{email_domain}'
        user = get_user_model().objects.create_user(
            email=email,
            password=self.password
        )
        normalized_email = f'{email_identifier}@{email_domain.lower()}'
        self.assertEqual(user.email, normalized_email)

    def test_user_invalid_email(self):
        """Test creating user with no email provided raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, self.password)

    def test_create_new_superuser(self):
        """Test creating a new superuser"""
        user = get_user_model().objects.create_superuser(
            email=self.email,
            password=self.password)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """Test the tag string representation"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Vegan'
        )

        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        """Test the ingredient string representation"""
        ingredient = models.Ingredient.objects.create(
            user=sample_user(),
            name='Pork Ribs'
        )

        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        """Test the recipe string representation"""
        recipe = models.Recipe.objects.create(
            user=sample_user(),
            title='Steak and mushroom sauce',
            time_minutes=5,
            price=5.00
        )

        self.assertEqual(str(recipe), recipe.title)

    @patch('uuid.uuid4')
    def test_recipe_file_path_uuid(self, mock_uuid):
        """Test recipe image is stored in the correct location"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'myimage.jpg')
        exp_path = f'uploads/recipe{os.sep}{uuid}.jpg'  # expected path

        self.assertEqual(file_path, exp_path)
