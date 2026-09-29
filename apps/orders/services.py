from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.audit.services import record_event
from apps.inventory.models import StockBalance, StockMovement
from apps.inventory.services import InsufficientStockError, register_movement

from .models import GiftRequest, GiftRequestItem


def _items_for_update(gift_request):
    return list(
        GiftRequestItem.objects.select_for_update()
        .select_related("product")
        .filter(request=gift_request)
        .order_by("product_id")
    )


@transaction.atomic
def submit_request(gift_request: GiftRequest) -> GiftRequest:
    gift_request = GiftRequest.objects.select_for_update().get(pk=gift_request.pk)
    if gift_request.status != GiftRequest.Status.DRAFT:
        raise ValueError("Somente rascunhos podem ser enviados.")
    if not gift_request.items.exists():
        raise ValueError("A solicitação precisa ter ao menos um item.")
    gift_request.status = GiftRequest.Status.SUBMITTED
    gift_request.submitted_at = timezone.now()
    gift_request.save(update_fields=["status", "submitted_at", "updated_at"])
    record_event(
        action="orders.request_submitted", entity=gift_request, actor=gift_request.requester
    )
    return gift_request


@transaction.atomic
def approve_request(gift_request: GiftRequest, approver) -> GiftRequest:
    gift_request = GiftRequest.objects.select_for_update().get(pk=gift_request.pk)
    if gift_request.status != GiftRequest.Status.SUBMITTED:
        raise ValueError("Somente solicitações enviadas podem ser aprovadas.")
    gift_request.status = GiftRequest.Status.APPROVED
    gift_request.approved_by = approver
    gift_request.approved_at = timezone.now()
    gift_request.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    record_event(action="orders.request_approved", entity=gift_request, actor=approver)
    return gift_request


@transaction.atomic
def reject_request(gift_request: GiftRequest, rejected_by, reason: str) -> GiftRequest:
    gift_request = GiftRequest.objects.select_for_update().get(pk=gift_request.pk)
    if gift_request.status not in {GiftRequest.Status.SUBMITTED, GiftRequest.Status.APPROVED}:
        raise ValueError("Somente solicitações enviadas ou aprovadas podem ser rejeitadas.")
    reason = reason.strip()
    if len(reason) < 3:
        raise ValueError("Informe um motivo de rejeição.")
    gift_request.status = GiftRequest.Status.REJECTED
    gift_request.rejection_reason = reason
    gift_request.approved_by = rejected_by
    gift_request.approved_at = timezone.now()
    gift_request.save(
        update_fields=["status", "rejection_reason", "approved_by", "approved_at", "updated_at"]
    )
    record_event(
        action="orders.request_rejected",
        entity=gift_request,
        actor=rejected_by,
        metadata={"reason": reason},
    )
    return gift_request


@transaction.atomic
def cancel_request(gift_request: GiftRequest, cancelled_by) -> GiftRequest:
    gift_request = GiftRequest.objects.select_for_update().get(pk=gift_request.pk)
    if gift_request.status in {
        GiftRequest.Status.FULFILLED,
        GiftRequest.Status.REJECTED,
        GiftRequest.Status.CANCELLED,
    }:
        raise ValueError("Esta solicitação não pode mais ser cancelada.")
    items = _items_for_update(gift_request)
    for item in items:
        if item.reserved_quantity:
            balance = StockBalance.objects.select_for_update().get(product=item.product)
            balance.reserved_quantity -= item.reserved_quantity
            balance.save(update_fields=["reserved_quantity", "updated_at"])
            item.reserved_quantity = 0
            item.save(update_fields=["reserved_quantity"])
    gift_request.status = GiftRequest.Status.CANCELLED
    gift_request.save(update_fields=["status", "updated_at"])
    record_event(action="orders.request_cancelled", entity=gift_request, actor=cancelled_by)
    return gift_request


@transaction.atomic
def reserve_request(gift_request: GiftRequest, reserved_by=None) -> GiftRequest:
    gift_request = GiftRequest.objects.select_for_update().get(pk=gift_request.pk)
    if gift_request.status != GiftRequest.Status.APPROVED:
        raise ValueError("Somente solicitações aprovadas podem ser reservadas.")

    items = _items_for_update(gift_request)
    for item in items:
        balance, _ = StockBalance.objects.select_for_update().get_or_create(product=item.product)
        available = balance.quantity - balance.reserved_quantity
        if available < item.remaining_quantity:
            raise InsufficientStockError(f"Estoque insuficiente para o produto {item.product.sku}.")
        balance.reserved_quantity += item.remaining_quantity
        balance.save(update_fields=["reserved_quantity", "updated_at"])
        item.reserved_quantity += item.remaining_quantity
        item.save(update_fields=["reserved_quantity"])

    gift_request.status = GiftRequest.Status.RESERVED
    gift_request.save(update_fields=["status", "updated_at"])
    record_event(action="orders.request_reserved", entity=gift_request, actor=reserved_by)
    return gift_request


@transaction.atomic
def fulfill_request(gift_request: GiftRequest, fulfilled_by, quantities=None) -> GiftRequest:
    gift_request = GiftRequest.objects.select_for_update().get(pk=gift_request.pk)
    allowed = {GiftRequest.Status.RESERVED, GiftRequest.Status.PARTIALLY_FULFILLED}
    if gift_request.status not in allowed:
        raise ValueError("Somente solicitações reservadas podem ser atendidas.")

    items = _items_for_update(gift_request)
    fulfilled_any = False
    for item in items:
        remaining = item.remaining_quantity
        requested_amount = remaining
        if quantities is not None:
            requested_amount = int(quantities.get(str(item.id), 0))
        if requested_amount < 0 or requested_amount > remaining:
            raise ValueError("A quantidade de atendimento é inválida.")
        if requested_amount == 0:
            continue
        if item.reserved_quantity < requested_amount:
            raise ValueError("O item não possui reserva suficiente para atendimento.")

        fulfilled_any = True
        register_movement(
            product=item.product,
            movement_type=StockMovement.MovementType.EXIT,
            quantity_delta=-requested_amount,
            created_by=fulfilled_by,
            reference=str(gift_request.id),
            note="Baixa por atendimento de solicitação",
        )
        balance = StockBalance.objects.select_for_update().get(product=item.product)
        balance.reserved_quantity -= requested_amount
        balance.save(update_fields=["reserved_quantity", "updated_at"])
        item.fulfilled_quantity += requested_amount
        item.reserved_quantity -= requested_amount
        item.save(update_fields=["fulfilled_quantity", "reserved_quantity"])

    if not fulfilled_any:
        raise ValueError("Informe ao menos uma quantidade maior que zero para atendimento.")
    all_fulfilled = not GiftRequestItem.objects.filter(
        request=gift_request, fulfilled_quantity__lt=F("quantity")
    ).exists()
    gift_request.status = (
        GiftRequest.Status.FULFILLED if all_fulfilled else GiftRequest.Status.PARTIALLY_FULFILLED
    )
    gift_request.save(update_fields=["status", "updated_at"])
    record_event(action="orders.request_fulfilled", entity=gift_request, actor=fulfilled_by)
    return gift_request
