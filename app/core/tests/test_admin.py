from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

class AdminSiteTests(TestCase):

  def setUp(self):
    self.client = Client()
    self.admin_user = get_user_model().objects.create_superuser(
      email='superuser@gmail.com',
      password='Testpass123'
    )
    self.client.force_login(self.admin_user)
    self.user = get_user_model().objects.create_user(
      email='user@gmail.com',
      password='Testpass123',
      name='Basic user'
    )

  def test_users_listed(self):
    """Test that all users are listed in the user page"""
    url = reverse('admin:core_user_changelist')
    res = self.client.get(url)

    self.assertContains(res, self.user.name)
    self.assertContains(res, self.user.email)