from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.catalog.models import Product

from .models import StockBalance
from .services import InsufficientStockError, register_movement


class StockMovementServiceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="stock@example.com", username="stock", password="strong-password-123"
        )
        self.product = Product.objects.create(sku="CAN-001", name="Caneca")

    def test_entry_then_exit_updates_available_balance(self):
        register_movement(
            product=self.product,
            movement_type="entry",
            quantity_delta=10,
            created_by=self.user,
        )
        register_movement(
            product=self.product,
            movement_type="exit",
            quantity_delta=-3,
            created_by=self.user,
        )

        balance = StockBalance.objects.get(product=self.product)
        self.assertEqual(balance.quantity, 7)
        self.assertEqual(balance.available_quantity, 7)

    def test_exit_cannot_make_balance_negative(self):
        with self.assertRaises(InsufficientStockError):
            register_movement(
                product=self.product,
                movement_type="exit",
                quantity_delta=-1,
                created_by=self.user,
            )


class StockMovementApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="stock-api@example.com", username="stock-api", password="strong-password-123"
        )
        self.client.force_authenticate(self.user)
        self.product = Product.objects.create(sku="GARR-001", name="Garrafa")

    def test_can_register_entry_from_api(self):
        response = self.client.post(
            reverse("stock-movement-list"),
            {
                "product": str(self.product.id),
                "movement_type": "entry",
                "quantity_delta": 5,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(StockBalance.objects.get(product=self.product).quantity, 5)

