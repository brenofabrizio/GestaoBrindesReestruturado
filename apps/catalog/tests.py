from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import Category, Product


class CatalogApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="catalog@example.com", username="catalog", password="strong-password-123"
        )
        self.client.force_authenticate(self.user)

    def test_can_create_and_list_product(self):
        category = Category.objects.create(name="Eventos")
        response = self.client.post(
            reverse("product-list"),
            {"sku": "CAN-001", "name": "Caneca", "category": str(category.id)},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Product.objects.count(), 1)

