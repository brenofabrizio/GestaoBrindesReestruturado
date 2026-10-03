from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.catalog.models import Product

from .models import StockBalance, StockMovement
from .services import InsufficientStockError, register_movement

TEST_PASSWORD = "not-a-real-credential-for-tests"


class StockMovementServiceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="stock@example.com", username="stock", password=TEST_PASSWORD
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
            email="stock-api@example.com",
            username="stock-api",
            password=TEST_PASSWORD,
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_authenticate(self.user)
        self.product = Product.objects.create(sku="GARR-001", name="Garrafa")

    def test_cd_operator_can_confirm_with_qr_but_cannot_authorize_a_new_exit(self):
        from apps.accounts.models import UserProfile

        register_movement(
            product=self.product,
            movement_type="entry",
            quantity_delta=5,
            created_by=self.user,
        )
        order_response = self.client.post(
            "/api/v1/inventory/exit-orders/",
            {"product": str(self.product.id), "quantity": 2, "note": "Retirada"},
            format="json",
        )
        self.assertEqual(order_response.status_code, 201)
        self.assertTrue(order_response.data["qr_token"])

        other_authorizer = User.objects.create_user(
            email="other-authorizer@example.com", username="other-authorizer", password=TEST_PASSWORD
        )
        other_authorizer.profile.role = UserProfile.Role.APPROVER
        other_authorizer.profile.save(update_fields=["role"])
        self.client.force_authenticate(other_authorizer)
        other_list = self.client.get("/api/v1/inventory/exit-orders/")
        self.assertEqual(other_list.status_code, 200)
        self.assertIsNone(other_list.data[0]["qr_token"])

        cd_user = User.objects.create_user(
            email="cd@example.com", username="cd", password=TEST_PASSWORD
        )
        cd_user.profile.role = UserProfile.Role.OPERATOR
        cd_user.profile.save(update_fields=["role"])
        self.client.force_authenticate(cd_user)

        list_response = self.client.get("/api/v1/inventory/exit-orders/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data), 1)
        self.assertNotIn("qr_token", list_response.data[0])

        confirm = self.client.post(
            "/api/v1/inventory/exit-orders/confirm-by-qr/",
            {"qr_token": order_response.data["qr_token"]},
            format="json",
        )
        self.assertEqual(confirm.status_code, 200)
        self.assertEqual(StockBalance.objects.get(product=self.product).quantity, 3)

        create = self.client.post(
            "/api/v1/inventory/exit-orders/",
            {"product": str(self.product.id), "quantity": 1, "note": "Unauthorized"},
            format="json",
        )
        self.assertEqual(create.status_code, 403)

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

    def test_cancelling_pending_exit_releases_reservation_without_debit(self):
        register_movement(
            product=self.product,
            movement_type="entry",
            quantity_delta=5,
            created_by=self.user,
        )
        order = self.client.post(
            "/api/v1/inventory/exit-orders/",
            {"product": str(self.product.id), "quantity": 3, "note": "Cancelável"},
            format="json",
        )
        self.assertEqual(order.status_code, 201)

        cancel_url = f"/api/v1/inventory/exit-orders/{order.data['id']}/cancel/"
        cancelled = self.client.post(cancel_url, {}, format="json")
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.data["status"], "cancelled")
        balance = StockBalance.objects.get(product=self.product)
        self.assertEqual(balance.quantity, 5)
        self.assertEqual(balance.reserved_quantity, 0)
        self.assertEqual(StockMovement.objects.filter(movement_type="exit").count(), 0)

        repeated = self.client.post(cancel_url, {}, format="json")
        self.assertEqual(repeated.status_code, 200)
        balance.refresh_from_db()
        self.assertEqual(balance.quantity, 5)
        self.assertEqual(balance.reserved_quantity, 0)

    def test_application_admin_can_cancel_another_users_pending_exit(self):
        from apps.accounts.models import UserProfile

        register_movement(
            product=self.product,
            movement_type="entry",
            quantity_delta=5,
            created_by=self.user,
        )
        order = self.client.post(
            "/api/v1/inventory/exit-orders/",
            {"product": str(self.product.id), "quantity": 2, "note": "Outro solicitante"},
            format="json",
        )
        self.assertEqual(order.status_code, 201)

        admin = User.objects.create_user(
            email="admin-profile@example.com", username="admin-profile", password=TEST_PASSWORD
        )
        admin.profile.role = UserProfile.Role.ADMIN
        admin.profile.save(update_fields=["role"])
        self.client.force_authenticate(admin)
        cancelled = self.client.post(
            f"/api/v1/inventory/exit-orders/{order.data['id']}/cancel/", {}, format="json"
        )
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.data["status"], "cancelled")
        self.assertEqual(StockBalance.objects.get(product=self.product).reserved_quantity, 0)

    def test_exit_is_reserved_then_debited_once_after_cd_confirmation(self):
        from .models import StockExitOrder

        register_movement(
            product=self.product,
            movement_type="entry",
            quantity_delta=5,
            created_by=self.user,
        )
        response = self.client.post(
            "/api/v1/inventory/exit-orders/",
            {"product": str(self.product.id), "quantity": 3, "note": "Evento"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        balance = StockBalance.objects.get(product=self.product)
        self.assertEqual(balance.quantity, 5)
        self.assertEqual(balance.reserved_quantity, 3)

        order_id = response.data["id"]
        confirm_url = f"/api/v1/inventory/exit-orders/{order_id}/confirm/"
        wrong_token = self.client.post(confirm_url, {"qr_token": "wrong"}, format="json")
        self.assertEqual(wrong_token.status_code, 400)
        balance.refresh_from_db()
        self.assertEqual(balance.quantity, 5)
        self.assertEqual(balance.reserved_quantity, 3)
        self.assertEqual(StockMovement.objects.filter(movement_type="exit").count(), 0)

        confirmed = self.client.post(confirm_url, {"qr_token": response.data["qr_token"]}, format="json")
        self.assertEqual(confirmed.status_code, 200)
        balance.refresh_from_db()
        self.assertEqual(balance.quantity, 2)
        self.assertEqual(balance.reserved_quantity, 0)
        self.assertEqual(StockMovement.objects.filter(movement_type="exit").count(), 1)

        repeated = self.client.post(confirm_url, {"qr_token": response.data["qr_token"]}, format="json")
        self.assertEqual(repeated.status_code, 200)
        balance.refresh_from_db()
        self.assertEqual(balance.quantity, 2)
        self.assertEqual(StockMovement.objects.filter(movement_type="exit").count(), 1)

    def test_direct_exit_movement_is_rejected_in_favor_of_confirmation_flow(self):
        register_movement(
            product=self.product,
            movement_type="entry",
            quantity_delta=5,
            created_by=self.user,
        )
        response = self.client.post(
            reverse("stock-movement-list"),
            {"product": str(self.product.id), "movement_type": "exit", "quantity_delta": -2},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(StockBalance.objects.get(product=self.product).quantity, 5)


class IndustryStockApiTests(APITestCase):
    def setUp(self):
        from apps.catalog.models import Industry

        self.user = User.objects.create_user(
            email="industry-stock@example.com",
            username="industry-stock",
            password=TEST_PASSWORD,
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_authenticate(self.user)
        self.industry = Industry.objects.create(name="Movement Industry")
        self.product = Product.objects.create(sku="IND-001", name="Brinde por indústria")

    def add_movement_for(self, industry, quantity=8):
        response = self.client.post(
            reverse("stock-movement-list"),
            {
                "product": str(self.product.id),
                "movement_type": "entry",
                "quantity_delta": quantity,
                "industry": str(industry.id),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        return response

    def create_industry_user(self):
        from apps.accounts.models import UserProfile

        user = User.objects.create_user(
            email="sector-user@example.com",
            username="sector-user",
            password=TEST_PASSWORD,
        )
        user.profile.role = UserProfile.Role.INDUSTRY
        user.profile.industry = self.industry
        user.profile.save(update_fields=["role", "industry"])
        self.client.force_authenticate(user)
        return user

    def test_industry_user_cannot_read_global_stock_balance(self):
        self.add_movement_for(self.industry)
        self.create_industry_user()
        response = self.client.get("/api/v1/inventory/balances/")
        self.assertEqual(response.status_code, 403)

    def test_industry_user_sees_only_its_movements_and_industry(self):
        from apps.catalog.models import Industry

        other = Industry.objects.create(name="Other Movement Industry")
        self.add_movement_for(self.industry, 8)
        self.add_movement_for(other, 13)
        self.create_industry_user()
        movements = self.client.get("/api/v1/inventory/movements/")
        industries = self.client.get("/api/v1/catalog/industries/")
        self.assertEqual(movements.status_code, 200)
        self.assertEqual(industries.status_code, 200)
        self.assertEqual(len(movements.data), 1)
        self.assertEqual(movements.data[0]["industry"], self.industry.id)
        self.assertEqual(len(industries.data), 1)
        self.assertEqual(industries.data[0]["id"], str(self.industry.id))

    def test_industry_balance_report_is_scoped_and_aggregated(self):
        from apps.catalog.models import Industry

        other = Industry.objects.create(name="Second Movement Industry")
        self.add_movement_for(self.industry, 8)
        self.add_movement_for(other, 13)
        self.create_industry_user()
        response = self.client.get("/api/v1/inventory/industry-balances/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["industry_id"], str(self.industry.id))
        self.assertEqual(response.data[0]["quantity"], 8)

    def test_movement_api_persists_industry_attribution(self):
        response = self.client.post(
            reverse("stock-movement-list"),
            {
                "product": str(self.product.id),
                "movement_type": "entry",
                "quantity_delta": 8,
                "industry": str(self.industry.id),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data.get("industry"), self.industry.id)
        movement = StockMovement.objects.get(id=response.data["id"])
        self.assertEqual(movement.industry_id, self.industry.id)


class StockTransferApiTests(APITestCase):
    def setUp(self):
        from apps.catalog.models import Industry

        self.admin = User.objects.create_user(
            email="transfer-admin@example.com", username="transfer-admin", password="", is_superuser=True, is_staff=True
        )
        self.client.force_authenticate(self.admin)
        self.industry = Industry.objects.create(name="Transfer Industry")
        self.product = Product.objects.create(sku="TRANSFER-001", name="Transfer item")

    def test_transfer_moves_location_positions_without_changing_global_stock(self):
        cd = self.client.post("/api/v1/inventory/locations/", {"name": "CD principal", "kind": "cd"}, format="json")
        event = self.client.post("/api/v1/inventory/locations/", {"name": "Feirão", "kind": "event"}, format="json")
        self.assertEqual(cd.status_code, 201)
        self.assertEqual(event.status_code, 201)
        entry = self.client.post(
            "/api/v1/inventory/movements/",
            {"product": str(self.product.id), "industry": str(self.industry.id), "location": cd.data["id"], "movement_type": "entry", "quantity_delta": 10},
            format="json",
        )
        self.assertEqual(entry.status_code, 201)

        transfer = self.client.post(
            "/api/v1/inventory/transfers/",
            {"product": str(self.product.id), "industry_id": str(self.industry.id), "quantity": 6, "from_location_id": cd.data["id"], "to_location_id": event.data["id"]},
            format="json",
        )
        self.assertEqual(transfer.status_code, 201)
        balance = StockBalance.objects.get(product=self.product)
        self.assertEqual(balance.quantity, 10)
        self.assertEqual(transfer.data["movements"][0]["quantity_delta"], -6)
        self.assertEqual(transfer.data["movements"][1]["quantity_delta"], 6)

        positions = self.client.get(f"/api/v1/inventory/positions/?product_id={self.product.id}")
        self.assertEqual(positions.status_code, 200)
        by_location = {str(row["location"]["id"]): row["quantity"] for row in positions.data}
        self.assertEqual(by_location[str(cd.data["id"])], 4)
        self.assertEqual(by_location[str(event.data["id"])], 6)

        insufficient = self.client.post(
            "/api/v1/inventory/transfers/",
            {"product": str(self.product.id), "industry_id": str(self.industry.id), "quantity": 5, "from_location_id": cd.data["id"], "to_location_id": event.data["id"]},
            format="json",
        )
        self.assertEqual(insufficient.status_code, 400)
        balance.refresh_from_db()
        self.assertEqual(balance.quantity, 10)

    def test_transfer_rejects_inconsistent_global_and_location_balances(self):
        from apps.inventory.models import StockPosition

        cd = self.client.post("/api/v1/inventory/locations/", {"name": "CD auditoria", "kind": "cd"}, format="json")
        event = self.client.post("/api/v1/inventory/locations/", {"name": "Evento auditoria", "kind": "event"}, format="json")
        self.assertEqual(cd.status_code, 201)
        self.assertEqual(event.status_code, 201)
        self.client.post(
            "/api/v1/inventory/movements/",
            {"product": str(self.product.id), "industry": str(self.industry.id), "location": cd.data["id"], "movement_type": "entry", "quantity_delta": 10},
            format="json",
        )
        StockPosition.objects.filter(product=self.product, location_id=cd.data["id"]).update(quantity=9)

        response = self.client.post(
            "/api/v1/inventory/transfers/",
            {"product": str(self.product.id), "industry_id": str(self.industry.id), "quantity": 1, "from_location_id": cd.data["id"], "to_location_id": event.data["id"]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("reconcilie", response.data["detail"].lower())
        self.assertEqual(StockBalance.objects.get(product=self.product).quantity, 10)

    def test_transfer_cannot_move_units_reserved_for_exit_from_the_source_location(self):
        cd = self.client.post("/api/v1/inventory/locations/", {"name": "CD reserva", "kind": "cd"}, format="json")
        event = self.client.post("/api/v1/inventory/locations/", {"name": "Evento reserva", "kind": "event"}, format="json")
        self.assertEqual(cd.status_code, 201)
        self.assertEqual(event.status_code, 201)
        entry = self.client.post(
            "/api/v1/inventory/movements/",
            {"product": str(self.product.id), "industry": str(self.industry.id), "location": cd.data["id"], "movement_type": "entry", "quantity_delta": 10},
            format="json",
        )
        self.assertEqual(entry.status_code, 201)
        first_transfer = self.client.post(
            "/api/v1/inventory/transfers/",
            {"product": str(self.product.id), "industry_id": str(self.industry.id), "quantity": 7, "from_location_id": cd.data["id"], "to_location_id": event.data["id"]},
            format="json",
        )
        self.assertEqual(first_transfer.status_code, 201)
        order = self.client.post(
            "/api/v1/inventory/exit-orders/",
            {"product": str(self.product.id), "location": cd.data["id"], "quantity": 3, "note": "Reservada no CD"},
            format="json",
        )
        self.assertEqual(order.status_code, 201)

        blocked = self.client.post(
            "/api/v1/inventory/transfers/",
            {"product": str(self.product.id), "industry_id": str(self.industry.id), "quantity": 1, "from_location_id": cd.data["id"], "to_location_id": event.data["id"]},
            format="json",
        )

        self.assertEqual(blocked.status_code, 400)
        positions = self.client.get(f"/api/v1/inventory/positions/?product_id={self.product.id}")
        by_location = {str(row["location"]["id"]): row["quantity"] for row in positions.data}
        self.assertEqual(by_location[str(cd.data["id"])], 3)
        self.assertEqual(by_location[str(event.data["id"])], 7)
        balance = StockBalance.objects.get(product=self.product)
        self.assertEqual(balance.quantity, 10)
        self.assertEqual(balance.reserved_quantity, 3)

