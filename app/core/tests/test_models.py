from django.test import TestCase
from django.contrib.auth import get_user_model


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
