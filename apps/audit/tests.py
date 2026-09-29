from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import AuditEvent
from .services import record_event


class AuditTests(APITestCase):
    def test_event_records_actor_and_entity(self):
        actor = User.objects.create_user(
            email="audit@example.com", username="audit", password="strong-password-123"
        )
        event = record_event(action="test.created", entity=actor, actor=actor)

        self.assertEqual(event.actor, actor)
        self.assertEqual(event.entity_type, "accounts.user")
        self.assertEqual(AuditEvent.objects.count(), 1)

    def test_audit_api_filters_and_paginates_events(self):
        actor = User.objects.create_user(
            email="operator@example.com",
            username="operator",
            password="strong-password-123",
            is_superuser=True,
        )
        record_event(action="catalog.product_created", entity=actor, actor=actor)
        record_event(action="catalog.category_created", entity=actor, actor=actor)
        record_event(action="stock.entry_created", entity=actor, actor=actor)
        self.client.force_authenticate(actor)

        response = self.client.get(
            reverse("audit-event-list"), {"action": "catalog", "page_size": 1}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIn(
            response.data["results"][0]["action"],
            {"catalog.product_created", "catalog.category_created"},
        )

    def test_audit_api_rejects_invalid_filter_values(self):
        actor = User.objects.create_user(
            email="filter-admin@example.com",
            username="filter-admin",
            password="strong-password-123",
            is_superuser=True,
        )
        self.client.force_authenticate(actor)

        response = self.client.get(reverse("audit-event-list"), {"date_from": "not-a-date"})

        self.assertEqual(response.status_code, 400)
