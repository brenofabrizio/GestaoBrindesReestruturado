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

