from django.db import transaction

from apps.audit.services import record_event
from apps.catalog.models import Product

from .models import StockBalance, StockMovement


class InsufficientStockError(ValueError):
    """Raised when an exit would consume reserved or unavailable stock."""


@transaction.atomic
def register_movement(
    *,
    product: Product,
    movement_type: str,
    quantity_delta: int,
    created_by=None,
    reference: str = "",
    note: str = "",
) -> StockMovement:
    if quantity_delta == 0:
        raise ValueError("A movimentação não pode ter quantidade zero.")
    if movement_type == StockMovement.MovementType.ENTRY and quantity_delta < 0:
        raise ValueError("Entradas devem aumentar o saldo.")
    if movement_type == StockMovement.MovementType.EXIT and quantity_delta > 0:
        raise ValueError("Saídas devem reduzir o saldo.")

    balance, _ = StockBalance.objects.select_for_update().get_or_create(product=product)
    resulting_quantity = balance.quantity + quantity_delta
    if resulting_quantity < balance.reserved_quantity:
        raise InsufficientStockError("Saldo disponível insuficiente para a saída.")

    balance.quantity = resulting_quantity
    balance.save(update_fields=["quantity", "updated_at"])

    movement = StockMovement.objects.create(
        product=product,
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
        },
    )
    return movement
