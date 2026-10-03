import base64
import binascii
import hashlib
import json
import secrets

from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_event
from apps.inventory.models import StockBalance, StockMovement
from apps.inventory.services import default_cd_location, register_movement

from .models import (
    TradeDelivery,
    TradeDeliveryItem,
    TradeDeliverySequence,
    TradeRequest,
    TradeRequestHistory,
    TradeRequestItem,
)


@transaction.atomic
def create_trade_request(*, requester, industry, payload, items):
    total_value = sum((item.get("unit_value", 0) or 0) * item["qty_requested"] for item in items)
    trade_request = TradeRequest.objects.create(
        industry=industry,
        requester=requester,
        department=requester.profile.department,
        total_value=total_value,
        **payload,
    )
    TradeRequestItem.objects.bulk_create(
        [TradeRequestItem(request=trade_request, **item) for item in items]
    )
    TradeRequestHistory.objects.create(
        request=trade_request,
        from_status="",
        to_status=TradeRequest.Status.SOLICITADA,
        actor=requester,
        comment="Solicitação TRADE criada",
    )
    record_event(
        action="trade.request_created",
        entity=trade_request,
        actor=requester,
        metadata={"industry_id": str(industry.id), "public_code": trade_request.public_code},
    )
    return trade_request


def _transition_trade_request(trade_request, actor, next_status, comment):
    previous_status = trade_request.status
    trade_request.status = next_status
    trade_request.save(update_fields=["status", "updated_at"])
    TradeRequestHistory.objects.create(
        request=trade_request,
        from_status=previous_status,
        to_status=next_status,
        actor=actor,
        comment=comment,
    )


@transaction.atomic
def approve_trade_request(*, request_id, approver, purchase_ticket_no, notes=""):
    trade_request = TradeRequest.objects.select_for_update().get(pk=request_id)
    if trade_request.status != TradeRequest.Status.SOLICITADA:
        raise ValueError("Só é possível aprovar uma solicitação TRADE aguardando decisão.")
    purchase_ticket_no = purchase_ticket_no.strip()
    if not purchase_ticket_no:
        raise ValueError("Informe o chamado de compra.")

    trade_request.purchase_ticket_no = purchase_ticket_no
    trade_request.approved_by = approver
    trade_request.approved_at = timezone.now()
    trade_request.approval_notes = notes.strip()
    trade_request.save(
        update_fields=["purchase_ticket_no", "approved_by", "approved_at", "approval_notes", "updated_at"]
    )
    _transition_trade_request(
        trade_request,
        approver,
        TradeRequest.Status.COMPRA_REALIZADA,
        f"Aprovada. Chamado de compra: {purchase_ticket_no}",
    )
    _transition_trade_request(
        trade_request,
        approver,
        TradeRequest.Status.AGUARDANDO_RECEBIMENTO,
        "Aguardando chegada no CD para anexar a NF",
    )
    record_event(
        action="trade.request_approved",
        entity=trade_request,
        actor=approver,
        metadata={"purchase_ticket_no": purchase_ticket_no},
    )
    return trade_request


@transaction.atomic
def reject_trade_request(*, request_id, rejected_by, reason):
    trade_request = TradeRequest.objects.select_for_update().get(pk=request_id)
    if trade_request.status != TradeRequest.Status.SOLICITADA:
        raise ValueError("Só é possível reprovar uma solicitação TRADE aguardando decisão.")
    reason = reason.strip()
    if len(reason) < 3:
        raise ValueError("Informe o motivo da reprovação.")
    trade_request.rejection_reason = reason
    trade_request.save(update_fields=["rejection_reason", "updated_at"])
    _transition_trade_request(trade_request, rejected_by, TradeRequest.Status.REPROVADA, reason)
    record_event(
        action="trade.request_rejected",
        entity=trade_request,
        actor=rejected_by,
        metadata={"reason": reason},
    )
    return trade_request


@transaction.atomic
def receive_trade_request(*, request_id, receiver, invoice_no, items, notes=""):
    trade_request = TradeRequest.objects.select_for_update().select_related("industry").get(pk=request_id)
    allowed_statuses = {
        TradeRequest.Status.COMPRA_REALIZADA,
        TradeRequest.Status.AGUARDANDO_RECEBIMENTO,
        TradeRequest.Status.RECEBIDO_CD,
    }
    if trade_request.status not in allowed_statuses:
        raise ValueError("O CD só pode receber depois da aprovação e do chamado de compra.")
    invoice_no = invoice_no.strip()
    if not invoice_no:
        raise ValueError("Informe o número da NF no recebimento.")
    if not items:
        raise ValueError("Informe as quantidades recebidas por linha.")

    request_items = {
        item.product_id: item
        for item in TradeRequestItem.objects.select_for_update().filter(request=trade_request)
    }
    received_total = 0
    for line in items:
        product = line["item_id"]
        quantity = line["qty"]
        request_item = request_items.get(product.pk)
        if request_item is None:
            raise ValueError("O brinde informado não pertence a esta solicitação TRADE.")
        if quantity < 1 or request_item.qty_received + quantity > request_item.qty_requested:
            raise ValueError("A quantidade recebida excede o saldo solicitado para este brinde.")
        register_movement(
            product=product,
            industry=trade_request.industry,
            movement_type=StockMovement.MovementType.ENTRY,
            quantity_delta=quantity,
            created_by=receiver,
            location=default_cd_location(),
            reference=f"{trade_request.public_code}:{invoice_no}",
            note=f"Recebimento TRADE - NF {invoice_no}" + (f" - {notes.strip()}" if notes.strip() else ""),
        )
        request_item.qty_received += quantity
        request_item.save(update_fields=["qty_received"])
        received_total += quantity

    trade_request.invoice_no = invoice_no
    if trade_request.received_at is None:
        trade_request.received_at = timezone.now()
    trade_request.save(update_fields=["invoice_no", "received_at", "updated_at"])

    all_received = all(item.qty_received >= item.qty_requested for item in request_items.values())
    if trade_request.status == TradeRequest.Status.COMPRA_REALIZADA:
        _transition_trade_request(
            trade_request,
            receiver,
            TradeRequest.Status.AGUARDANDO_RECEBIMENTO,
            "NF informada no recebimento do CD",
        )
    if all_received:
        _transition_trade_request(
            trade_request,
            receiver,
            TradeRequest.Status.RECEBIDO_CD,
            "Todas as linhas recebidas no CD",
        )
        _transition_trade_request(
            trade_request,
            receiver,
            TradeRequest.Status.PRONTA,
            "Disponível para retirada",
        )
    record_event(
        action="trade.request_received",
        entity=trade_request,
        actor=receiver,
        metadata={"invoice_no": invoice_no, "quantity": received_total, "complete": all_received},
    )
    return trade_request


def _next_trade_delivery_code():
    year = timezone.localdate().year
    sequence, _ = TradeDeliverySequence.objects.select_for_update().get_or_create(
        year=year, defaults={"next_number": 1}
    )
    current_number = sequence.next_number
    sequence.next_number = current_number + 1
    sequence.save(update_fields=["next_number"])
    return f"PROT-{year}-{current_number:04d}"


@transaction.atomic
def withdraw_trade_request(
    *, request_id, delivered_by, public_code, idempotency_key, received_by_name, signature_data, items,
    received_by_document="", received_by_email="", received_by_phone="", recipient="", notes="",
):
    trade_request = TradeRequest.objects.select_for_update().select_related("industry").get(pk=request_id)
    public_code = public_code.strip()
    if not public_code.isascii() or not secrets.compare_digest(trade_request.public_code, public_code):
        raise ValueError("QR inválido para esta solicitação TRADE.")
    received_by_name = received_by_name.strip()
    if len(received_by_name) < 2:
        raise ValueError("Informe o nome de quem está retirando.")
    prefix, separator, encoded = signature_data.partition(",")
    if prefix != "data:image/png;base64" or not separator:
        raise ValueError("A assinatura deve ser uma imagem PNG capturada no comprovante.")
    try:
        signature_bytes = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("A assinatura PNG é inválida.") from exc
    if len(signature_bytes) < 32 or len(signature_bytes) > 1_000_000 or not signature_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("A assinatura PNG está vazia, inválida ou excede o limite de 1 MB.")
    if not items:
        raise ValueError("Informe as quantidades entregues por brinde.")
    idempotency_key = idempotency_key.strip()
    if len(idempotency_key) < 8 or len(idempotency_key) > 80 or not idempotency_key.isascii():
        raise ValueError("Informe uma chave de idempotência válida.")
    canonical_payload = {
        "public_code": public_code,
        "received_by_name": received_by_name,
        "received_by_document": received_by_document.strip(),
        "received_by_email": received_by_email.strip(),
        "received_by_phone": received_by_phone.strip(),
        "recipient": recipient.strip(),
        "signature_hash": hashlib.sha256(signature_data.encode()).hexdigest(),
        "notes": notes.strip(),
        "items": sorted(
            [{"item_id": str(line["item_id"].pk), "qty": int(line["qty"])} for line in items],
            key=lambda line: line["item_id"],
        ),
    }
    payload_hash = hashlib.sha256(
        json.dumps(canonical_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    previous_delivery = TradeDelivery.objects.select_for_update().filter(
        request=trade_request,
        idempotency_key=idempotency_key,
    ).first()
    if previous_delivery:
        if previous_delivery.payload_hash != payload_hash:
            raise ValueError("A chave de idempotência já foi usada com outro payload.")
        return previous_delivery
    if trade_request.status not in {TradeRequest.Status.PRONTA, TradeRequest.Status.RETIRADO}:
        raise ValueError("A retirada só pode ocorrer depois do recebimento completo no CD.")

    request_items = {
        item.product_id: item
        for item in TradeRequestItem.objects.select_for_update().filter(request=trade_request)
    }
    delivery = TradeDelivery.objects.create(
        code=_next_trade_delivery_code(),
        request=trade_request,
        idempotency_key=idempotency_key,
        payload_hash=payload_hash,
        delivered_by=delivered_by,
        received_by_name=received_by_name,
        received_by_document=received_by_document.strip(),
        received_by_email=received_by_email.strip(),
        received_by_phone=received_by_phone.strip(),
        recipient=recipient.strip(),
        signature_data=signature_data,
        notes=notes.strip(),
    )
    delivered_total = 0
    for line in items:
        product = line["item_id"]
        quantity = line["qty"]
        request_item = request_items.get(product.pk)
        if request_item is None:
            raise ValueError("O brinde informado não pertence a esta solicitação TRADE.")
        available_for_request = request_item.qty_received - request_item.qty_delivered
        if quantity < 1 or quantity > available_for_request:
            raise ValueError("A quantidade retirada excede o saldo recebido desta solicitação.")
        register_movement(
            product=product,
            industry=trade_request.industry,
            movement_type=StockMovement.MovementType.EXIT,
            quantity_delta=-quantity,
            created_by=delivered_by,
            location=default_cd_location(),
            reference=delivery.code,
            note=f"Retirada TRADE {trade_request.public_code} por QR",
        )
        balance = StockBalance.objects.select_for_update().get(product=product)
        TradeDeliveryItem.objects.create(
            delivery=delivery,
            request_item=request_item,
            quantity=quantity,
            balance_after=balance.quantity,
        )
        request_item.qty_delivered += quantity
        request_item.save(update_fields=["qty_delivered"])
        delivered_total += quantity

    if delivered_total == 0:
        raise ValueError("Informe ao menos uma quantidade maior que zero.")
    remaining = sum(item.qty_received - item.qty_delivered for item in request_items.values())
    if trade_request.status == TradeRequest.Status.PRONTA:
        _transition_trade_request(
            trade_request,
            delivered_by,
            TradeRequest.Status.RETIRADO,
            f"Protocolo {delivery.code}",
        )
    if remaining == 0:
        _transition_trade_request(
            trade_request,
            delivered_by,
            TradeRequest.Status.ENTREGUE,
            f"Protocolo {delivery.code}; saldo da solicitação zerado",
        )
    record_event(
        action="trade.request_withdrawn",
        entity=delivery,
        actor=delivered_by,
        metadata={"request_id": str(trade_request.id), "quantity": delivered_total, "code": delivery.code},
    )
    return delivery
