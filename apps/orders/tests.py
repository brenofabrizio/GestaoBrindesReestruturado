from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.catalog.models import Product
from apps.inventory.models import StockBalance
from apps.inventory.services import register_movement

from .models import GiftRequest, GiftRequestItem
from .services import (
    approve_request,
    fulfill_request,
    reject_request,
    reserve_request,
    submit_request,
)

TEST_PASSWORD = "not-a-real-credential-for-tests"


class GiftRequestWorkflowTests(APITestCase):
    def setUp(self):
        self.requester = User.objects.create_user(
            email="requester@example.com", username="requester", password=TEST_PASSWORD
        )
        self.operator = User.objects.create_user(
            email="operator@example.com",
            username="operator",
            password=TEST_PASSWORD,
            is_staff=True,
        )
        self.product = Product.objects.create(sku="KIT-001", name="Kit boas-vindas")
        register_movement(
            product=self.product,
            movement_type="entry",
            quantity_delta=10,
            created_by=self.operator,
        )
        self.gift_request = GiftRequest.objects.create(requester=self.requester)
        GiftRequestItem.objects.create(request=self.gift_request, product=self.product, quantity=3)

    def test_request_can_be_submitted_approved_reserved_and_fulfilled(self):
        submit_request(self.gift_request)
        approve_request(self.gift_request, self.operator)
        reserve_request(self.gift_request)
        fulfill_request(self.gift_request, self.operator)

        self.gift_request.refresh_from_db()
        balance = StockBalance.objects.get(product=self.product)
        self.assertEqual(self.gift_request.status, GiftRequest.Status.FULFILLED)
        self.assertEqual(balance.quantity, 7)
        self.assertEqual(balance.reserved_quantity, 0)

    def test_api_create_request_requires_items(self):
        self.client.force_authenticate(self.requester)
        response = self.client.post(
            reverse("gift-request-list"),
            {"justification": "Evento", "items": []},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_partial_fulfillment_keeps_remaining_reservation(self):
        submit_request(self.gift_request)
        approve_request(self.gift_request, self.operator)
        reserve_request(self.gift_request, self.operator)
        item = self.gift_request.items.get()

        fulfill_request(self.gift_request, self.operator, {str(item.id): 1})
        self.gift_request.refresh_from_db()
        balance = StockBalance.objects.get(product=self.product)
        self.assertEqual(self.gift_request.status, GiftRequest.Status.PARTIALLY_FULFILLED)
        self.assertEqual(balance.quantity, 9)
        self.assertEqual(balance.reserved_quantity, 2)

        fulfill_request(self.gift_request, self.operator)
        self.gift_request.refresh_from_db()
        balance.refresh_from_db()
        self.assertEqual(self.gift_request.status, GiftRequest.Status.FULFILLED)
        self.assertEqual(balance.reserved_quantity, 0)

    def test_fulfillment_rejects_zero_quantity_without_changing_status(self):
        submit_request(self.gift_request)
        approve_request(self.gift_request, self.operator)
        reserve_request(self.gift_request, self.operator)
        item = self.gift_request.items.get()

        with self.assertRaises(ValueError):
            fulfill_request(self.gift_request, self.operator, {str(item.id): 0})

        self.gift_request.refresh_from_db()
        balance = StockBalance.objects.get(product=self.product)
        self.assertEqual(self.gift_request.status, GiftRequest.Status.RESERVED)
        self.assertEqual(balance.quantity, 10)
        self.assertEqual(balance.reserved_quantity, 3)

    def test_rejection_keeps_stock_unchanged(self):
        submit_request(self.gift_request)
        reject_request(self.gift_request, self.operator, "Sem orçamento")

        self.gift_request.refresh_from_db()
        balance = StockBalance.objects.get(product=self.product)
        self.assertEqual(self.gift_request.status, GiftRequest.Status.REJECTED)
        self.assertEqual(balance.quantity, 10)

    def test_cancelling_reserved_request_releases_remaining_stock(self):
        from .services import cancel_request

        submit_request(self.gift_request)
        approve_request(self.gift_request, self.operator)
        reserve_request(self.gift_request, self.operator)

        cancel_request(self.gift_request, self.requester)

        balance = StockBalance.objects.get(product=self.product)
        item = self.gift_request.items.get()
        self.gift_request.refresh_from_db()
        self.assertEqual(self.gift_request.status, GiftRequest.Status.CANCELLED)
        self.assertEqual(balance.reserved_quantity, 0)
        self.assertEqual(balance.quantity, 10)
        self.assertEqual(item.reserved_quantity, 0)

    def test_approver_only_lists_requests_from_own_department(self):
        from apps.accounts.models import UserProfile

        approver = User.objects.create_user(
            email="approver@example.com", username="approver", password=TEST_PASSWORD
        )
        approver.profile.role = UserProfile.Role.APPROVER
        approver.profile.department = "Marketing"
        approver.profile.save()
        self.requester.profile.department = "Marketing"
        self.requester.profile.save()
        other_user = User.objects.create_user(
            email="other@example.com", username="other", password=TEST_PASSWORD
        )
        other_user.profile.department = "Financeiro"
        other_user.profile.save()
        visible = GiftRequest.objects.create(requester=self.requester)
        hidden = GiftRequest.objects.create(requester=other_user)
        self.client.force_authenticate(approver)

        response = self.client.get(reverse("gift-request-list"))

        self.assertEqual(response.status_code, 200)
        visible_ids = {row["id"] for row in response.data}
        self.assertIn(str(visible.id), visible_ids)
        self.assertNotIn(str(hidden.id), visible_ids)


class TradeRequestApiTests(APITestCase):
    def setUp(self):
        from apps.accounts.models import UserProfile
        from apps.catalog.models import Industry

        self.industry = Industry.objects.create(name="Indústria TRADE")
        self.other_industry = Industry.objects.create(name="Outra indústria TRADE")
        self.requester = User.objects.create_user(
            email="trade-industry@example.com", username="trade-industry", password=""
        )
        self.requester.profile.role = UserProfile.Role.INDUSTRY
        self.requester.profile.industry = self.industry
        self.requester.profile.save(update_fields=["role", "industry"])
        self.product = Product.objects.create(sku="TRADE-001", name="Brinde TRADE")

    def test_industry_can_create_trade_request_for_its_own_industry(self):
        self.client.force_authenticate(self.requester)

        response = self.client.post(
            "/api/v1/trade/requests/",
            {
                "industry_id": str(self.industry.id),
                "purpose": "Campanha de lançamento",
                "recipient": "Equipe de vendas",
                "action_type": "campanha",
                "items": [{"product": str(self.product.id), "qty_requested": 5, "unit_value": "12.50"}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "solicitada")
        self.assertEqual(response.data["industry_id"], self.industry.id)
        self.assertEqual(response.data["items"][0]["qty_requested"], 5)

    def test_industry_cannot_create_trade_request_for_another_industry(self):
        self.client.force_authenticate(self.requester)

        response = self.client.post(
            "/api/v1/trade/requests/",
            {
                "industry_id": str(self.other_industry.id),
                "purpose": "Fora do escopo",
                "items": [{"product": str(self.product.id), "qty_requested": 1}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def create_trade_request(self):
        self.client.force_authenticate(self.requester)
        response = self.client.post(
            "/api/v1/trade/requests/",
            {
                "industry_id": str(self.industry.id),
                "purpose": "Campanha de lançamento",
                "recipient": "Equipe de vendas",
                "action_type": "campanha",
                "items": [{"product": str(self.product.id), "qty_requested": 5, "unit_value": "12.50"}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        return response.data

    def create_approver(self):
        from apps.accounts.models import UserProfile

        approver = User.objects.create_user(
            email=f"approver-{User.objects.count()}@example.com", username=f"approver-{User.objects.count()}", password=""
        )
        approver.profile.role = UserProfile.Role.APPROVER
        approver.profile.department = "Marketing"
        approver.profile.save(update_fields=["role", "department"])
        return approver

    def test_approval_records_purchase_ticket_before_receipt(self):
        from apps.accounts.models import UserProfile

        self.requester.profile.department = "Marketing"
        self.requester.profile.save(update_fields=["department"])
        trade = self.create_trade_request()
        approver = self.create_approver()
        self.client.force_authenticate(approver)

        response = self.client.post(
            f"/api/v1/trade/requests/{trade['id']}/approve/",
            {"purchase_ticket_no": "COM-2026-55", "notes": "Aprovado"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "aguardando_recebimento")
        self.assertEqual(response.data["purchase_ticket_no"], "COM-2026-55")
        self.assertEqual(response.data["invoice_no"], "")
        self.assertEqual(response.data["approved_by"], approver.id)
        self.assertEqual(UserProfile.Role.APPROVER, approver.profile.role)

    def test_cd_queue_excludes_trade_requests_not_yet_approved(self):
        from apps.accounts.models import UserProfile

        self.requester.profile.department = "Marketing"
        self.requester.profile.save(update_fields=["department"])
        trade = self.create_trade_request()
        operator = User.objects.create_user(email="trade-queue-cd@example.com", username="trade-queue-cd", password="")
        operator.profile.role = UserProfile.Role.OPERATOR
        operator.profile.save(update_fields=["role"])
        self.client.force_authenticate(operator)

        response = self.client.get("/api/v1/trade/requests/")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(str(trade["id"]), {str(row["id"]) for row in response.data})

    def test_cd_can_receive_trade_partially_then_complete_against_invoice(self):
        from apps.accounts.models import UserProfile

        self.requester.profile.department = "Marketing"
        self.requester.profile.save(update_fields=["department"])
        trade = self.create_trade_request()
        approver = self.create_approver()
        self.client.force_authenticate(approver)
        approved = self.client.post(
            f"/api/v1/trade/requests/{trade['id']}/approve/",
            {"purchase_ticket_no": "COM-2026-56"},
            format="json",
        )
        self.assertEqual(approved.status_code, 200)

        operator = User.objects.create_user(
            email="trade-cd@example.com", username="trade-cd", password=""
        )
        operator.profile.role = UserProfile.Role.OPERATOR
        operator.profile.save(update_fields=["role"])
        self.client.force_authenticate(operator)
        receive_url = f"/api/v1/trade/requests/{trade['id']}/receive/"
        partial = self.client.post(
            receive_url,
            {"invoice_no": "NF-100", "items": [{"item_id": str(self.product.id), "qty": 2}]},
            format="json",
        )
        self.assertEqual(partial.status_code, 200)
        self.assertEqual(partial.data["status"], "aguardando_recebimento")
        self.assertEqual(partial.data["items"][0]["qty_received"], 2)
        from apps.inventory.models import StockMovement
        from apps.inventory.services import default_cd_location

        receipt_movement = StockMovement.objects.get(reference=f"{trade['public_code']}:NF-100")
        self.assertEqual(receipt_movement.location, default_cd_location())
        self.assertEqual(StockBalance.objects.get(product=self.product).quantity, 2)

        complete = self.client.post(
            receive_url,
            {"invoice_no": "NF-100", "items": [{"item_id": str(self.product.id), "qty": 3}]},
            format="json",
        )
        self.assertEqual(complete.status_code, 200)
        self.assertEqual(complete.data["status"], "pronta")
        self.assertEqual(complete.data["items"][0]["qty_received"], 5)
        balance = StockBalance.objects.get(product=self.product)
        self.assertEqual(balance.quantity, 5)
        self.assertEqual(balance.reserved_quantity, 0)
        cd_queue = self.client.get("/api/v1/trade/requests/")
        self.assertEqual(cd_queue.status_code, 200)
        self.assertIn(str(trade["id"]), {str(row["id"]) for row in cd_queue.data})

    def test_trade_withdrawal_requires_scanned_code_and_records_delivery(self):
        from apps.accounts.models import UserProfile

        self.requester.profile.department = "Marketing"
        self.requester.profile.save(update_fields=["department"])
        trade = self.create_trade_request()
        approver = self.create_approver()
        self.client.force_authenticate(approver)
        approved = self.client.post(
            f"/api/v1/trade/requests/{trade['id']}/approve/",
            {"purchase_ticket_no": "COM-SIGN-1"},
            format="json",
        )
        self.assertEqual(approved.status_code, 200)
        operator = User.objects.create_user(email="trade-sign-cd@example.com", username="trade-sign-cd", password="")
        operator.profile.role = UserProfile.Role.OPERATOR
        operator.profile.save(update_fields=["role"])
        self.client.force_authenticate(operator)
        receive = self.client.post(
            f"/api/v1/trade/requests/{trade['id']}/receive/",
            {"invoice_no": "NF-SIGN-1", "items": [{"item_id": str(self.product.id), "qty": 5}]},
            format="json",
        )
        self.assertEqual(receive.status_code, 200)
        payload = {
            "public_code": trade["public_code"],
            "idempotency_key": "trade-withdrawal-once",
            "received_by_name": "Destinatário de teste",
            "signature_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+c30cAAAAASUVORK5CYII=",
            "items": [{"item_id": str(self.product.id), "qty": 5}],
        }
        denied = self.client.post(f"/api/v1/trade/requests/{trade['id']}/withdraw/", {**payload, "public_code": "WRONG"}, format="json")
        self.assertEqual(denied.status_code, 400)
        self.assertEqual(StockBalance.objects.get(product=self.product).quantity, 5)
        delivered = self.client.post(f"/api/v1/trade/requests/{trade['id']}/withdraw/", payload, format="json")
        self.assertEqual(delivered.status_code, 200)
        self.assertEqual(delivered.data["status"], "entregue")
        self.assertEqual(delivered.data["deliveries"][0]["received_by_name"], "Destinatário de teste")
        self.assertRegex(delivered.data["deliveries"][0]["code"], r"^PROT-[0-9]{4}-[0-9]{4}$")
        from apps.inventory.models import StockMovement
        from apps.inventory.services import default_cd_location

        delivery_movement = StockMovement.objects.get(reference=delivered.data["deliveries"][0]["code"])
        self.assertEqual(delivery_movement.location, default_cd_location())
        self.assertEqual(StockBalance.objects.get(product=self.product).quantity, 0)

    def test_replayed_partial_trade_withdrawal_is_idempotent(self):
        from apps.accounts.models import UserProfile
        from apps.orders.models import TradeRequestItem

        self.requester.profile.department = "Marketing"
        self.requester.profile.save(update_fields=["department"])
        trade = self.create_trade_request()
        approver = self.create_approver()
        self.client.force_authenticate(approver)
        self.client.post(
            f"/api/v1/trade/requests/{trade['id']}/approve/",
            {"purchase_ticket_no": "COM-IDEM-1"},
            format="json",
        )
        operator = User.objects.create_user(email="trade-idem-cd@example.com", username="trade-idem-cd", password="")
        operator.profile.role = UserProfile.Role.OPERATOR
        operator.profile.save(update_fields=["role"])
        self.client.force_authenticate(operator)
        self.client.post(
            f"/api/v1/trade/requests/{trade['id']}/receive/",
            {"invoice_no": "NF-IDEM-1", "items": [{"item_id": str(self.product.id), "qty": 5}]},
            format="json",
        )
        payload = {
            "public_code": trade["public_code"],
            "idempotency_key": "withdrawal-attempt-1",
            "received_by_name": "Destinatário de teste",
            "signature_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+c30cAAAAASUVORK5CYII=",
            "items": [{"item_id": str(self.product.id), "qty": 2}],
        }
        url = f"/api/v1/trade/requests/{trade['id']}/withdraw/"
        first = self.client.post(url, payload, format="json")
        replay = self.client.post(url, payload, format="json")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(first.data["deliveries"][0]["code"], replay.data["deliveries"][0]["code"])
        changed_payload = {**payload, "items": [{"item_id": str(self.product.id), "qty": 3}]}
        conflict = self.client.post(url, changed_payload, format="json")
        self.assertEqual(conflict.status_code, 400)
        self.assertEqual(StockBalance.objects.get(product=self.product).quantity, 3)
        item = TradeRequestItem.objects.get(request_id=trade["id"], product=self.product)
        self.assertEqual(item.qty_delivered, 2)
