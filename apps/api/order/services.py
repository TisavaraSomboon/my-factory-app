"""All business logic for orders. Views and serializers only call these functions.

Rule ids (R1, R2, R3) and stage names refer to docs/SPEC.md section 6.
Every state change runs in a transaction with the order row locked.
"""
import json
from datetime import timedelta
from decimal import Decimal
from typing import Any, Callable

from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.catalog.models import Color, Inspection, Pattern
from apps.common.exceptions import DomainError

from .choices import NEXT_STATUS, REJECT_TARGET, STAGE_SLA_HOURS, EventAction, OrderStatus
from .models import Order, OrderEvent
from .rules import allowed_fabrics, is_fabric_allowed

# Fields a client may change with PATCH, and only while the order is in DESIGN (R2).
UPDATABLE_FIELDS = (
    "name", "address", "quantity", "pattern", "color", "color_metric", "fabric_type", "garment_type",
)


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def _jsonable(data: dict[str, Any]) -> dict[str, Any]:
    """Make a payload safe to store in a JSONField (Decimal -> str, etc.)."""
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))


def _lock(order: Order) -> Order:
    """Re-read the order with a row lock. Must be called inside transaction.atomic()."""
    return Order.objects.select_for_update().get(pk=order.pk)


def _log(order: Order, action: str, actor: str, note: str = "", data: dict[str, Any] | None = None,
         status: str | None = None) -> OrderEvent:
    """Append one event to the order timeline."""
    return OrderEvent.objects.create(
        order=order, status=status or order.status, action=action, actor=actor, note=note,
        data=_jsonable(data or {}),
    )


def _move_to(order: Order, new_status: str) -> None:
    """Change status and restart the SLA clock (even when the status is unchanged)."""
    order.status = new_status
    order.stage_started_at = timezone.now()


def _validation_error(message: str, **details: Any) -> DomainError:
    return DomainError("VALIDATION_ERROR", message, details)


def _require_positive(value: Any, field: str) -> Decimal:
    """Return value as Decimal if it is > 0, otherwise raise VALIDATION_ERROR."""
    if value is None or Decimal(str(value)) <= 0:
        raise _validation_error(f"{field} is required and must be greater than 0.", field=field)
    return Decimal(str(value))


def _check_fabric(garment_type: str, fabric_type: str) -> None:
    """R1: raise FABRIC_INCOMPATIBLE if the fabric is not allowed for the garment."""
    if not is_fabric_allowed(garment_type, fabric_type):
        raise DomainError(
            "FABRIC_INCOMPATIBLE",
            f"{fabric_type} cannot be used for {garment_type} garments.",
            {"garment_type": garment_type, "fabric_type": fabric_type,
             "allowed_fabrics": allowed_fabrics(garment_type)},
        )


def _ensure_design_stage(order: Order) -> None:
    """R2/R3: raise ORDER_LOCKED unless the order is still in DESIGN."""
    if order.status != OrderStatus.DESIGN:
        raise DomainError(
            "ORDER_LOCKED", "Order can only be changed or deleted while in DESIGN.",
            {"status": order.status},
        )


# --------------------------------------------------------------------------
# Create / update / delete
# --------------------------------------------------------------------------
@transaction.atomic
def create_order(actor: str | None = None, **fields: Any) -> Order:
    """R1: create an order in DESIGN after checking fabric compatibility. Logs CREATED."""
    _check_fabric(fields["garment_type"], fields["fabric_type"])
    order = Order.objects.create(status=OrderStatus.DESIGN, stage_started_at=timezone.now(), **fields)
    _log(order, EventAction.CREATED, actor or order.requester_username, data={"name": order.name})
    return order


@transaction.atomic
def update_order(order: Order, actor: str | None = None, **changes: Any) -> Order:
    """R2: edit an order only while DESIGN; R1 is re-checked. Logs UPDATED."""
    order = _lock(order)
    _ensure_design_stage(order)
    for field, value in changes.items():
        if field in UPDATABLE_FIELDS:
            setattr(order, field, value)
    _check_fabric(order.garment_type, order.fabric_type)
    order.save()
    changed = {k: getattr(v, "pk", v) for k, v in changes.items() if k in UPDATABLE_FIELDS}
    _log(order, EventAction.UPDATED, actor or order.requester_username, data=changed)
    return order


@transaction.atomic
def delete_order(order: Order) -> None:
    """R3: delete an order only while DESIGN."""
    order = _lock(order)
    _ensure_design_stage(order)
    order.delete()


# --------------------------------------------------------------------------
# Approve: one gate function per stage, each returns the data it stored
# --------------------------------------------------------------------------
def _gate_design(order: Order, data: dict[str, Any]) -> dict[str, Any]:
    """DESIGN gate: a pattern must be attached (or supplied as pattern_id)."""
    pattern_id = data.get("pattern_id")
    if pattern_id is not None:
        pattern = Pattern.objects.filter(pk=pattern_id).first()
        if pattern is None:
            raise _validation_error("pattern_id does not exist.", pattern_id=pattern_id)
        order.pattern = pattern
    if order.pattern_id is None:
        raise DomainError("PATTERN_REQUIRED", "A pattern is required to approve the design.")
    return {}


def _gate_fabric_prep(order: Order, data: dict[str, Any]) -> dict[str, Any]:
    """FABRIC_PREP gate: swatch must match the ordered fabric and be allowed (R1); meters > 0."""
    swatch = data.get("swatch_fabric_type")
    if not swatch or swatch != order.fabric_type:
        raise DomainError(
            "SWATCH_MISMATCH", "Swatch fabric must equal the order's fabric type.",
            {"swatch_fabric_type": swatch, "fabric_type": order.fabric_type},
        )
    _check_fabric(order.garment_type, swatch)
    meters = _require_positive(data.get("measured_fabric_meters"), "measured_fabric_meters")
    order.measured_fabric_meters = meters
    return {}


def _gate_fabric_done(order: Order, data: dict[str, Any]) -> dict[str, Any]:
    """FABRIC_DONE gate: color required; 0 < finished meters <= measured meters."""
    color_id = data.get("color_id")
    if color_id is not None:
        color = Color.objects.filter(pk=color_id).first()
        if color is None:
            raise _validation_error("color_id does not exist.", color_id=color_id)
        order.color = color
    if order.color_id is None:
        raise DomainError("COLOR_REQUIRED", "A color is required to finish the fabric.")
    finished = _require_positive(data.get("finished_fabric_meters"), "finished_fabric_meters")
    measured = order.measured_fabric_meters
    if measured is not None and finished > measured:
        raise DomainError(
            "YIELD_EXCEEDS_MEASURED", "Finished fabric cannot exceed measured fabric.",
            {"finished_fabric_meters": str(finished), "measured_fabric_meters": str(measured)},
        )
    order.finished_fabric_meters = finished
    return {}


def _gate_stitching(order: Order, data: dict[str, Any]) -> dict[str, Any]:
    """STITCHING gate: assembled pieces must equal the ordered quantity."""
    count = data.get("assembled_pieces_count")
    if count != order.quantity:
        raise DomainError(
            "PIECE_COUNT_MISMATCH", "Assembled pieces must equal the order quantity.",
            {"assembled_pieces_count": count, "quantity": order.quantity},
        )
    order.assembled_pieces_count = count
    return {}


def _gate_qa(order: Order, data: dict[str, Any]) -> dict[str, Any]:
    """QA gate: every inspection for the garment type answered, and all passed."""
    required_ids = set(
        Inspection.objects.filter(garment_type=order.garment_type).values_list("id", flat=True)
    )
    results = data.get("results") or []
    answers = {int(r["inspection_id"]): bool(r["passed"]) for r in results}
    unknown = set(answers) - required_ids
    if unknown:
        raise _validation_error("Unknown inspection ids for this garment type.", unknown=sorted(unknown))
    missing = required_ids - set(answers)
    if missing:
        raise DomainError(
            "INSPECTION_INCOMPLETE", "Every inspection for this garment type must be answered.",
            {"missing_inspection_ids": sorted(missing)},
        )
    failed = sorted(i for i, passed in answers.items() if not passed)
    if failed:
        raise DomainError(
            "QC_FAILED", "Some inspections failed; reject the order instead.",
            {"failed_inspection_ids": failed},
        )
    return {"results": results}


def _gate_packaging(order: Order, data: dict[str, Any]) -> dict[str, Any]:
    """PACKAGING gate: must be ready for dispatch and have a tracking number."""
    if not order.is_ready_dispatch:
        raise DomainError("NOT_READY_FOR_DISPATCH", "Order is not marked ready for dispatch.")
    tracking = (data.get("tracking_number") or "").strip()
    if not tracking:
        raise _validation_error("tracking_number is required.", field="tracking_number")
    order.tracking_number = tracking
    return {}


def _gate_delivered(order: Order, data: dict[str, Any]) -> dict[str, Any]:
    """DELIVERED is terminal."""
    raise DomainError("ORDER_COMPLETED", "Order is already delivered.")


STAGE_GATES: dict[str, Callable[[Order, dict[str, Any]], dict[str, Any]]] = {
    OrderStatus.DESIGN: _gate_design,
    OrderStatus.FABRIC_PREP: _gate_fabric_prep,
    OrderStatus.FABRIC_DONE: _gate_fabric_done,
    OrderStatus.STITCHING: _gate_stitching,
    OrderStatus.QA: _gate_qa,
    OrderStatus.PACKAGING: _gate_packaging,
    OrderStatus.DELIVERED: _gate_delivered,
}


@transaction.atomic
def approve(order: Order, actor: str, note: str = "", **data: Any) -> Order:
    """Pass the gate of the current stage, then advance to the next status. Logs APPROVED."""
    order = _lock(order)
    stage = order.status
    STAGE_GATES[stage](order, data)
    _move_to(order, NEXT_STATUS[stage])
    order.save()
    payload = {k: v for k, v in data.items() if v is not None}
    _log(order, EventAction.APPROVED, actor, note, data=payload, status=stage)
    return order


# --------------------------------------------------------------------------
# Reject and ready-dispatch
# --------------------------------------------------------------------------
@transaction.atomic
def reject(order: Order, actor: str, reason: str) -> Order:
    """Send the order back per REJECT_TARGET, rework_count + 1. Logs REJECTED."""
    order = _lock(order)
    origin = order.status
    target = REJECT_TARGET[origin]
    if target is None:
        raise DomainError(
            "REJECT_NOT_ALLOWED", f"Orders in {origin} cannot be rejected.", {"status": origin}
        )
    if not (reason or "").strip():
        raise _validation_error("reason is required.", field="reason")
    _move_to(order, target)
    order.rework_count += 1
    order.save()
    _log(order, EventAction.REJECTED, actor, reason, data={"from": origin, "to": target}, status=origin)
    return order


@transaction.atomic
def set_ready_dispatch(order: Order, actor: str, is_ready: bool, cartons_count: int | None = None) -> Order:
    """PACKAGING only: mark ready (needs cartons >= 1) or hold in staging. Logs READY_DISPATCH_SET."""
    order = _lock(order)
    if order.status != OrderStatus.PACKAGING:
        raise DomainError(
            "INVALID_STAGE", "Ready-dispatch can only be set during PACKAGING.", {"status": order.status}
        )
    if is_ready:
        if cartons_count is None or cartons_count < 1:
            raise _validation_error("cartons_count must be >= 1 when ready.", field="cartons_count")
        order.cartons_count = cartons_count
    order.is_ready_dispatch = is_ready
    order.save()
    _log(order, EventAction.READY_DISPATCH_SET, actor,
         data={"is_ready": is_ready, "cartons_count": cartons_count})
    return order


# --------------------------------------------------------------------------
# Queries
# --------------------------------------------------------------------------
def overdue_condition(now=None) -> Q:
    """SQL version of Order.is_overdue: stage_started_at + stage SLA is already in the past."""
    now = now or timezone.now()
    condition = Q(pk__in=[])
    for status, hours in STAGE_SLA_HOURS.items():
        if hours is not None:
            condition |= Q(status=status, stage_started_at__lt=now - timedelta(hours=hours))
    return condition


def filter_overdue(queryset: QuerySet[Order], overdue: bool) -> QuerySet[Order]:
    """Keep only overdue (True) or only not-overdue (False) orders."""
    condition = overdue_condition()
    return queryset.filter(condition) if overdue else queryset.exclude(condition)
