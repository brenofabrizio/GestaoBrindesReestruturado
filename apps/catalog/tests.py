from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.audit.models import AuditEvent

from .models import Category, Product

TEST_PASSWORD = "not-a-real-credential-for-tests"


class CatalogApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="catalog@example.com",
            username="catalog",
            password=TEST_PASSWORD,
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_admin_can_create_and_list_industries(self):
        response = self.client.post(
            "/api/v1/catalog/industries/",
            {"name": "Indústria Alfa"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Indústria Alfa")
        listed = self.client.get("/api/v1/catalog/industries/")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.data), 1)

    def test_can_create_and_list_product(self):
        category = Category.objects.create(name="Eventos")
        response = self.client.post(
            reverse("product-list"),
            {"sku": "CAN-001", "name": "Caneca", "category": str(category.id)},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Product.objects.count(), 1)

    def test_delete_product_deactivates_it_and_keeps_audit_trail(self):
        product = Product.objects.create(sku="SAFE-001", name="Histórico preservado")

        response = self.client.delete(reverse("product-detail", args=[product.id]))

        product.refresh_from_db()
        self.assertEqual(response.status_code, 204)
        self.assertFalse(product.is_active)
        self.assertTrue(AuditEvent.objects.filter(action="catalog.product_deactivated").exists())
