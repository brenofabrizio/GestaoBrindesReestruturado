import secrets

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.audit.services import record_event
from apps.catalog.models import Product

from .models import (
    StockBalance,
    StockExitOrder,
    StockLocation,
    StockMovement,
    StockPosition,
    StockTransfer,
)


class InsufficientStockError(ValueError):
    """Raised when an exit would consume reserved or unavailable stock."""


def default_cd_location() -> StockLocation:
    location, _ = StockLocation.objects.get_or_create(
        name="CD Belford Roxo",
        defaults={"kind": StockLocation.Kind.CD},
    )
    return location


@transaction.atomic
def transfer_stock(*, product: Product, industry, quantity: int, from_location: StockLocation, to_location: StockLocation, created_by, notes="") -> StockTransfer:
    if quantity <= 0:
        raise ValueError("A quantidade transferida deve ser maior que zero.")
    if from_location.pk == to_location.pk:
        raise ValueError("O local de origem deve ser diferente do destino.")
    if not product.is_active or not from_location.is_active or not to_location.is_active or not industry.is_active:
        raise ValueError("Produto, indústria e locais precisam estar ativos.")

    balance, _ = StockBalance.objects.select_for_update().get_or_create(product=product)
    if quantity > balance.available_quantity:
        raise InsufficientStockError("Saldo global disponível insuficiente para a transferência.")

    locations = sorted([from_location, to_location], key=lambda location: str(location.pk))
    positions = {}
    for location in locations:
        position, _ = StockPosition.objects.select_for_update().get_or_create(
            product=product,
            location=location,
            defaults={"quantity": 0},
        )
        positions[location.pk] = position
    position_total = (
        StockPosition.objects.filter(product=product).aggregate(total=Sum("quantity"))["total"] or 0
    )
    if position_total != balance.quantity:
        raise ValueError("As posições por local divergem do saldo global; reconcilie antes de transferir.")

    source = positions[from_location.pk]
    destination = positions[to_location.pk]
    reserved_at_source = (
        StockExitOrder.objects.filter(
            product=product,
            location=from_location,
            status=StockExitOrder.Status.PENDING,
        ).aggregate(total=Sum("quantity"))["total"]
        or 0
    )
    source_available = max(0, source.quantity - reserved_at_source)
    if quantity > source_available:
        raise InsufficientStockError("A transferência não pode mover unidades reservadas para saída neste local.")

    source.quantity -= quantity
    destination.quantity += quantity
    source.save(update_fields=["quantity", "updated_at"])
    destination.save(update_fields=["quantity", "updated_at"])

    transfer = StockTransfer.objects.create(
        product=product,
        industry=industry,
        quantity=quantity,
        from_location=from_location,
        to_location=to_location,
        created_by=created_by,
        notes=notes,
    )
    for location, delta in ((from_location, -quantity), (to_location, quantity)):
        StockMovement.objects.create(
            product=product,
            industry=industry,
            location=location,
            to_location=to_location,
            transfer=transfer,
            movement_type=StockMovement.MovementType.TRANSFER,
            quantity_delta=delta,
            created_by=created_by,
            reference=str(transfer.id),
            note=notes,
        )
    record_event(
        action="inventory.stock_transferred",
        entity=transfer,
        actor=created_by,
        metadata={
            "industry_id": str(industry.id),
            "product_id": str(product.id),
            "quantity": quantity,
            "from_location_id": str(from_location.id),
            "to_location_id": str(to_location.id),
        },
    )
    return transfer


@transaction.atomic
def register_movement(
    *,
    product: Product,
    movement_type: str,
    quantity_delta: int,
    created_by=None,
    reference: str = "",
    note: str = "",
    industry=None,
    location: StockLocation | None = None,
) -> StockMovement:
    if quantity_delta == 0:
        raise ValueError("A movimentação não pode ter quantidade zero.")
    if movement_type == StockMovement.MovementType.TRANSFER:
        raise ValueError("Use o endpoint de transferência para mover estoque entre locais.")
    if movement_type == StockMovement.MovementType.ENTRY and quantity_delta < 0:
        raise ValueError("Entradas devem aumentar o saldo.")
    if movement_type == StockMovement.MovementType.EXIT and quantity_delta > 0:
        raise ValueError("Saídas devem reduzir o saldo.")

    location = location or default_cd_location()
    if not location.is_active:
        raise ValueError("Não é possível movimentar estoque em um local inativo.")
    balance, _ = StockBalance.objects.select_for_update().get_or_create(product=product)
    position, _ = StockPosition.objects.select_for_update().get_or_create(
        product=product,
        location=location,
        defaults={"quantity": 0},
    )
    resulting_position = position.quantity + quantity_delta
    if resulting_position < 0:
        raise InsufficientStockError("Saldo insuficiente no local para a movimentação.")

    resulting_quantity = balance.quantity + quantity_delta
    if resulting_quantity < balance.reserved_quantity:
        raise InsufficientStockError("Saldo disponível insuficiente para a saída.")

    balance.quantity = resulting_quantity
    balance.save(update_fields=["quantity", "updated_at"])
    position.quantity = resulting_position
    position.save(update_fields=["quantity", "updated_at"])

    movement = StockMovement.objects.create(
        product=product,
        industry=industry,
        location=location,
        movement_type=movement_type,
        quantity_delta=quantity_delta,
        created_by=created_by,
        reference=reference,
        note=note,
    )
    record_event(
        action="inventory.movement_registered",
        entity=movement,
        actor=created_by,
        metadata={
            "product_id": str(product.id),
            "movement_type": movement_type,
            "quantity_delta": quantity_delta,
            "reference": reference,
            "industry_id": str(industry.id) if industry else None,
        },
    )
    return movement


@transaction.atomic
def create_exit_order(*, product: Product, quantity: int, requested_by, note: str = "", industry=None, location=None) -> StockExitOrder:
    if quantity <= 0:
        raise ValueError("A quantidade de saída deve ser maior que zero.")

    balance, _ = StockBalance.objects.select_for_update().get_or_create(product=product)
    if balance.quantity - balance.reserved_quantity < quantity:
        raise InsufficientStockError("Saldo disponível insuficiente para reservar a saída.")
    location = location or default_cd_location()
    position, _ = StockPosition.objects.select_for_update().get_or_create(
        product=product, location=location, defaults={"quantity": 0}
    )
    if position.quantity < quantity:
        raise InsufficientStockError("Saldo insuficiente neste local para reservar a saída.")

    balance.reserved_quantity += quantity
    balance.save(update_fields=["reserved_quantity", "updated_at"])
    order = StockExitOrder.objects.create(
        product=product,
        industry=industry,
        location=location,
        quantity=quantity,
        note=note,
        requested_by=requested_by,
    )
    record_event(
        action="inventory.exit_order_created",
        entity=order,
        actor=requested_by,
        metadata={
            "product_id": str(product.id),
            "industry_id": str(industry.id) if industry else None,
            "quantity": quantity,
        },
    )
    return order


@transaction.atomic
def confirm_exit_order(*, order: StockExitOrder, confirmed_by, qr_token: str) -> StockExitOrder:
    order = StockExitOrder.objects.select_for_update().get(pk=order.pk)
    token_matches = (
        isinstance(qr_token, str)
        and qr_token.isascii()
        and secrets.compare_digest(str(order.qr_token), qr_token)
    )
    if not token_matches:
        raise ValueError("O QR informado não corresponde à saída pendente.")
    if order.status == StockExitOrder.Status.CONFIRMED:
        return order
    if order.status != StockExitOrder.Status.PENDING:
        raise ValueError("Somente saídas pendentes podem ser confirmadas.")

    balance = StockBalance.objects.select_for_update().get(product=order.product)
    if balance.reserved_quantity < order.quantity:
        raise ValueError("A reserva de estoque da saída não está consistente.")
    balance.reserved_quantity -= order.quantity
    balance.save(update_fields=["reserved_quantity", "updated_at"])

    register_movement(
        product=order.product,
        industry=order.industry,
        movement_type=StockMovement.MovementType.EXIT,
        quantity_delta=-order.quantity,
        created_by=confirmed_by,
        reference=f"exit-order:{order.pk}",
        note=order.note,
        location=order.location or default_cd_location(),
    )
    order.status = StockExitOrder.Status.CONFIRMED
    order.confirmed_by = confirmed_by
    order.confirmed_at = timezone.now()
    order.save(update_fields=["status", "confirmed_by", "confirmed_at"])
    record_event(
        action="inventory.exit_order_confirmed",
        entity=order,
        actor=confirmed_by,
        metadata={"quantity": order.quantity},
    )
    return order


@transaction.atomic
def cancel_exit_order(*, order: StockExitOrder, cancelled_by) -> StockExitOrder:
    order = StockExitOrder.objects.select_for_update().get(pk=order.pk)
    if order.status == StockExitOrder.Status.CANCELLED:
        return order
    if order.status != StockExitOrder.Status.PENDING:
        raise ValueError("Somente saídas pendentes podem ser canceladas.")
    is_admin = cancelled_by.is_superuser or (
        getattr(getattr(cancelled_by, "profile", None), "role", None) == UserProfile.Role.ADMIN
    )
    if order.requested_by_id != cancelled_by.id and not is_admin:
        raise ValueError("Somente o autor da ordem ou um administrador pode cancelá-la.")

    balance = StockBalance.objects.select_for_update().get(product=order.product)
    if balance.reserved_quantity < order.quantity:
        raise ValueError("A reserva de estoque da saída não está consistente.")
    balance.reserved_quantity -= order.quantity
    balance.save(update_fields=["reserved_quantity", "updated_at"])

    order.status = StockExitOrder.Status.CANCELLED
    order.save(update_fields=["status"])
    record_event(
        action="inventory.exit_order_cancelled",
        entity=order,
        actor=cancelled_by,
        metadata={"quantity": order.quantity},
    )
    return order
