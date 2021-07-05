from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient


CREATE_USER_URL = reverse('user:create')
GET_TOKEN_URL = reverse('user:token')


def create_user(**params):
    """Helper function to create new user"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the User API"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_successful(self):
        """Test creating using with a valid payload is successful"""
        payload = {
            'email': 'sample@gmail.com',
            'password': 'Testpass123',
            'name': 'Basic user'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """Test creating a user that already exists fail"""
        payload = {
            'email': 'sample@gmail.com',
            'password': 'Testpass123',
            'name': 'Basic user',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that password must be more than 5 characters"""
        payload = {
            'email': 'sample@gmail.com',
            'password': 'pw',
            'name': 'Basic user',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_token_created_for_valid_user_credentials(self):
        """Test token is generated for valid user"""
        payload = {'email': 'sample@gmail.com', 'password': 'Testpass123'}
        create_user(**payload)
        res = self.client.post(GET_TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_token_not_created_for_invalid_user_credentials(self):
        """Test token is NOT generated for invalid user credentials"""
        payload = {'email': 'sample@gmail.com', 'password': 'Testpass123'}
        create_user(**payload)
        invalid_credential_payload = {
            'email': 'sample@gmail.com',
            'password': 'wrongpassword'
        }
        res = self.client.post(GET_TOKEN_URL, invalid_credential_payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_not_created_for_invalid_user(self):
        """Test token is NOT generated for invalid user"""
        payload = {'email': 'sample@gmail.com', 'password': 'Testpass123'}
        res = self.client.post(GET_TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_not_created_for_missing_user_credentials(self):
        """Test token is not generated for missing user credentials"""
        payload = {'email': 'sample@gmail.com', 'password': ''}
        res = self.client.post(GET_TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
