from django.urls import reverse
from rest_framework.test import APITestCase

from .access import has_permission
from .models import User

TEST_PASSWORD = "not-a-real-credential-for-tests"


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            password=TEST_PASSWORD,
        )

    def test_can_obtain_jwt_and_read_current_user(self):
        token_response = self.client.post(
            reverse("token-obtain"),
            {"email": "admin@example.com", "password": TEST_PASSWORD},
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

    def test_stock_operations_profile_cannot_manage_catalog_or_process_internal_requests(self):
        from .models import UserProfile

        operations = User.objects.create_user(
            email="cd@example.com", username="cd", password=""
        )
        operations.profile.role = UserProfile.Role.OPERATOR
        operations.profile.save()

        self.assertFalse(has_permission(operations, "catalog.manage"))
        self.assertFalse(has_permission(operations, "requests.create"))
        self.assertFalse(has_permission(operations, "requests.approve"))
        self.assertFalse(has_permission(operations, "requests.process"))
        self.assertFalse(has_permission(operations, "requests.view_all"))
        self.assertTrue(has_permission(operations, "stock.entry"))
        self.assertTrue(has_permission(operations, "stock.transfer"))
        self.assertTrue(has_permission(operations, "stock.receive"))
        self.assertTrue(has_permission(operations, "stock.exit_confirm"))

    def test_legacy_operations_slug_cannot_manage_catalog_or_internal_requests(self):
        operations = User.objects.create_user(
            email="operations@example.com", username="operations", password=""
        )
        operations.profile.role = "operations"
        operations.profile.save()

        self.assertFalse(has_permission(operations, "catalog.manage"))
        self.assertFalse(has_permission(operations, "requests.view_all"))
        self.assertFalse(has_permission(operations, "requests.process"))
        self.assertTrue(has_permission(operations, "stock.receive"))

    def test_admin_can_assign_an_industry_to_a_user_profile(self):
        from apps.catalog.models import Industry

        industry = Industry.objects.create(name="Industry Assignment")
        target = User.objects.create_user(
            email="industry-user@example.com", username="industry-user", password=""
        )
        admin = User.objects.create_user(
            email="profile-admin@example.com",
            username="profile-admin",
            password="",
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_authenticate(admin)
        response = self.client.patch(
            f"/api/v1/auth/profiles/{target.profile.id}/",
            {"role": "industry", "industry": str(industry.id)},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        target.profile.refresh_from_db()
        self.assertEqual(target.profile.role, "industry")
        self.assertEqual(target.profile.industry_id, industry.id)

    def test_approver_can_decide_but_cannot_process_cd_requests(self):
        from .models import UserProfile

        approver = User.objects.create_user(
            email="approver@example.com", username="approver", password=""
        )
        approver.profile.role = UserProfile.Role.APPROVER
        approver.profile.save()

        self.assertTrue(has_permission(approver, "requests.approve"))
        self.assertFalse(has_permission(approver, "requests.process"))

    def test_industry_profile_can_view_industry_inventory(self):
        from .models import UserProfile

        industry_user = User.objects.create_user(
            email="industry@example.com", username="industry", password=""
        )
        industry_user.profile.role = UserProfile.Role.INDUSTRY
        industry_user.profile.save()

        self.assertTrue(has_permission(industry_user, "stock.view"))
