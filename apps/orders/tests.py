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


class GiftRequestWorkflowTests(APITestCase):
    def setUp(self):
        self.requester = User.objects.create_user(
            email="requester@example.com", username="requester", password="strong-password-123"
        )
        self.operator = User.objects.create_user(
            email="operator@example.com",
            username="operator",
            password="strong-password-123",
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
            email="approver@example.com", username="approver", password="strong-password-123"
        )
        approver.profile.role = UserProfile.Role.APPROVER
        approver.profile.department = "Marketing"
        approver.profile.save()
        self.requester.profile.department = "Marketing"
        self.requester.profile.save()
        other_user = User.objects.create_user(
            email="other@example.com", username="other", password="strong-password-123"
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
