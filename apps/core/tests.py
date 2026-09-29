from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Product
from apps.core.management.commands.import_legacy import Command
from apps.inventory.models import StockBalance


class HealthCheckTests(TestCase):
    def test_health_check_is_public(self):
        response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")


class LegacyImportValidationTests(TestCase):
    def test_apply_resolves_references_ignoring_case_and_surrounding_spaces(self):
        payload = {
            "source_version": "1",
            "users": [],
            "categories": [{"name": "Brindes"}],
            "items": [{"code": "KIT-1", "name": "Kit", "category": "brindes"}],
            "stock": [{"code": " kit-1 ", "qty_on_hand": 10, "qty_reserved": 0}],
        }

        self.assertEqual(Command.validate_payload(payload), [])
        Command.apply_payload(payload)

        product = Product.objects.get(sku="KIT-1")
        self.assertEqual(product.category.name, "Brindes")
        self.assertEqual(StockBalance.objects.get(product=product).quantity, 10)

    def test_invalid_stock_quantities_return_validation_errors(self):
        payload = {
            "source_version": "1",
            "users": [],
            "categories": [],
            "items": [{"code": "KIT-1", "name": "Kit"}],
            "stock": [{"code": "KIT-1", "qty_on_hand": "indefinido", "qty_reserved": 2}],
        }

        errors = Command.validate_payload(payload)

        self.assertTrue(
            any("quantidade" in error.lower() or "saldo" in error.lower() for error in errors)
        )

    def test_duplicate_stock_rows_are_rejected(self):
        payload = {
            "source_version": "1",
            "users": [],
            "categories": [],
            "items": [{"code": "KIT-1", "name": "Kit"}],
            "stock": [
                {"code": "KIT-1", "qty_on_hand": 5, "qty_reserved": 0},
                {"code": "KIT-1", "qty_on_hand": 8, "qty_reserved": 0},
            ],
        }

        errors = Command.validate_payload(payload)

        self.assertTrue(any("duplicado" in error.lower() for error in errors))
