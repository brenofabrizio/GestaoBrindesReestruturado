from django.urls import reverse
from rest_framework.test import APITestCase

from .access import has_permission
from .models import User


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="strong-password-123",
        )

    def test_can_obtain_jwt_and_read_current_user(self):
        token_response = self.client.post(
            reverse("token-obtain"),
            {"email": "admin@example.com", "password": "strong-password-123"},
            format="json",
        )
        self.assertEqual(token_response.status_code, 200)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.json()['access']}"
        )
        response = self.client.get(reverse("me"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "admin@example.com")
        self.assertEqual(response.json()["profile"]["role"], "requester")

    def test_requester_cannot_approve(self):
        self.assertTrue(has_permission(self.user, "requests.create"))
        self.assertFalse(has_permission(self.user, "requests.approve"))
