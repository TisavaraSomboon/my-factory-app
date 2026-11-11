from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.common.exceptions import DomainError, http_status_for
from apps.orders import services
from apps.orders.choices import NEXT_STATUS, REJECT_TARGET, STAGE_SLA_HOURS, EventAction, OrderStatus
from apps.orders.models import Order
from conftest import make_color, make_inspection, make_order, make_pattern, order_at

pytestmark = pytest.mark.django_db


def code_of(exc_info) -> str:
    return exc_info.value.code


# ---- Create / R1 -------------------------------------------------------
def test_create_logs_event_and_starts_in_design():
    order = make_order()
    assert order.status == OrderStatus.DESIGN
    assert [e.action for e in order.events.all()] == [EventAction.CREATED]


def test_r1_fabric_incompatible_on_create():
    with pytest.raises(DomainError) as e:
        make_order(garment_type="HEAT_INSULATION", fabric_type="POLYESTER")
    assert code_of(e) == "FABRIC_INCOMPATIBLE"
    assert Order.objects.count() == 0


# ---- Update / delete (R2, R3) ------------------------------------------
def test_r2_update_in_design_logs_updated():
    order = make_order()
    order = services.update_order(order, name="New name", quantity=9)
    assert order.name == "New name"
    assert order.events.last().action == EventAction.UPDATED


def test_r2_update_rechecks_r1():
    order = make_order(garment_type="GENERAL", fabric_type="POLYESTER")
    with pytest.raises(DomainError) as e:
        services.update_order(order, garment_type="HEAT_INSULATION")
    assert code_of(e) == "FABRIC_INCOMPATIBLE"


def test_r2_update_locked_after_design():
    order = order_at("FABRIC_PREP")
    with pytest.raises(DomainError) as e:
        services.update_order(order, name="x")
    assert code_of(e) == "ORDER_LOCKED"


def test_r3_delete_in_design():
    order = make_order()
    services.delete_order(order)
    assert Order.objects.count() == 0


def test_r3_delete_locked_after_design():
    order = order_at("FABRIC_PREP")
    with pytest.raises(DomainError) as e:
        services.delete_order(order)
    assert code_of(e) == "ORDER_LOCKED"


# ---- Approve gates -----------------------------------------------------
def test_design_requires_pattern():
    order = make_order()
    with pytest.raises(DomainError) as e:
        services.approve(order, "a")
    assert code_of(e) == "PATTERN_REQUIRED"


def test_design_accepts_pattern_id_in_payload():
    order = make_order()
    order = services.approve(order, "a", pattern_id=make_pattern().pk)
    assert order.status == OrderStatus.FABRIC_PREP and order.pattern_id


def test_design_uses_pattern_already_on_order():
    order = make_order(pattern=make_pattern())
    assert services.approve(order, "a").status == OrderStatus.FABRIC_PREP


def test_fabric_prep_swatch_mismatch():
    order = order_at("FABRIC_PREP")
    with pytest.raises(DomainError) as e:
        services.approve(order, "a", swatch_fabric_type="LINEN", measured_fabric_meters="5")
    assert code_of(e) == "SWATCH_MISMATCH"


def test_fabric_prep_missing_swatch_is_mismatch():
    order = order_at("FABRIC_PREP")
    with pytest.raises(DomainError) as e:
        services.approve(order, "a", measured_fabric_meters="5")
    assert code_of(e) == "SWATCH_MISMATCH"


def test_fabric_prep_swatch_must_be_allowed():
    # Order is GENERAL/POLYESTER, then garment cannot change after DESIGN, so
    # force an incompatible combination directly in the database.
    order = order_at("FABRIC_PREP")
    Order.objects.filter(pk=order.pk).update(garment_type="HEAT_INSULATION", fabric_type="POLYESTER")
    with pytest.raises(DomainError) as e:
        services.approve(order, "a", swatch_fabric_type="POLYESTER", measured_fabric_meters="5")
    assert code_of(e) == "FABRIC_INCOMPATIBLE"


@pytest.mark.parametrize("meters", [None, "0", "-1"])
def test_fabric_prep_meters_must_be_positive(meters):
    order = order_at("FABRIC_PREP")
    data = {"swatch_fabric_type": "COTTON"}
    if meters is not None:
        data["measured_fabric_meters"] = meters
    with pytest.raises(DomainError) as e:
        services.approve(order, "a", **data)
    assert code_of(e) == "VALIDATION_ERROR"


def test_fabric_prep_stores_meters():
    order = order_at("FABRIC_PREP")
    order = services.approve(order, "a", swatch_fabric_type="COTTON", measured_fabric_meters="12.5")
    assert order.measured_fabric_meters == Decimal("12.5")
    assert order.status == OrderStatus.FABRIC_DONE


def test_fabric_done_requires_color():
    order = order_at("FABRIC_DONE")
    with pytest.raises(DomainError) as e:
        services.approve(order, "a", finished_fabric_meters="5")
    assert code_of(e) == "COLOR_REQUIRED"


def test_fabric_done_yield_exceeds_measured():
    order = order_at("FABRIC_DONE")  # measured 20
    with pytest.raises(DomainError) as e:
        services.approve(order, "a", color_id=make_color("#AABBCC").pk, finished_fabric_meters="20.01")
    assert code_of(e) == "YIELD_EXCEEDS_MEASURED"


def test_fabric_done_finished_must_be_positive():
    order = order_at("FABRIC_DONE")
    with pytest.raises(DomainError) as e:
        services.approve(order, "a", color_id=make_color("#AABBCC").pk, finished_fabric_meters="0")
    assert code_of(e) == "VALIDATION_ERROR"


def test_fabric_done_ok_equal_to_measured():
    order = order_at("FABRIC_DONE")
    order = services.approve(order, "a", color_id=make_color("#AABBCC").pk, finished_fabric_meters="20")
    assert order.status == OrderStatus.STITCHING


def test_stitching_piece_count_mismatch():
    order = order_at("STITCHING")
    with pytest.raises(DomainError) as e:
        services.approve(order, "a", assembled_pieces_count=order.quantity - 1)
    assert code_of(e) == "PIECE_COUNT_MISMATCH"


def test_stitching_ok():
    order = order_at("STITCHING")
    order = services.approve(order, "a", assembled_pieces_count=order.quantity)
    assert order.status == OrderStatus.QA and order.assembled_pieces_count == order.quantity


def test_qa_incomplete_results():
    make_inspection(name="A")
    make_inspection(name="B")
    order = order_at("QA")
    from apps.catalog.models import Inspection
    one = Inspection.objects.first()
    with pytest.raises(DomainError) as e:
        services.approve(order, "a", results=[{"inspection_id": one.pk, "passed": True}])
    assert code_of(e) == "INSPECTION_INCOMPLETE"


def test_qa_failed_item():
    insp = make_inspection()
    order = order_at("QA")
    with pytest.raises(DomainError) as e:
        services.approve(order, "a", results=[{"inspection_id": insp.pk, "passed": False}])
    assert code_of(e) == "QC_FAILED"


def test_qa_unknown_inspection_is_validation_error():
    order = order_at("QA")
    with pytest.raises(DomainError) as e:
        services.approve(order, "a", results=[{"inspection_id": 9999, "passed": True}])
    assert code_of(e) == "VALIDATION_ERROR"


def test_qa_without_inspections_allowed():
    order = order_at("QA")
    assert services.approve(order, "a").status == OrderStatus.PACKAGING


def test_qa_results_saved_in_event():
    insp = make_inspection()
    order = order_at("QA")
    services.approve(order, "a", results=[{"inspection_id": insp.pk, "passed": True}])
    event = order.events.filter(action=EventAction.APPROVED).last()
    assert event.status == OrderStatus.QA
    assert event.data["results"] == [{"inspection_id": insp.pk, "passed": True}]


def test_packaging_not_ready():
    order = order_at("PACKAGING")
    with pytest.raises(DomainError) as e:
        services.approve(order, "a", tracking_number="T1")
    assert code_of(e) == "NOT_READY_FOR_DISPATCH"


def test_packaging_requires_tracking_number():
    order = services.set_ready_dispatch(order_at("PACKAGING"), "a", True, 2)
    with pytest.raises(DomainError) as e:
        services.approve(order, "a")
    assert code_of(e) == "VALIDATION_ERROR"


def test_delivered_cannot_be_approved():
    order = order_at("PACKAGING")
    order = services.set_ready_dispatch(order, "a", True, 2)
    order = services.approve(order, "a", tracking_number="T1")
    assert order.status == OrderStatus.DELIVERED and order.tracking_number == "T1"
    with pytest.raises(DomainError) as e:
        services.approve(order, "a")
    assert code_of(e) == "ORDER_COMPLETED"


def test_full_happy_path_events():
    insp = make_inspection()
    order = order_at("QA")
    order = services.approve(order, "qa", results=[{"inspection_id": insp.pk, "passed": True}])
    order = services.set_ready_dispatch(order, "pk", True, 4)
    order = services.approve(order, "pk", tracking_number="TH1")
    assert order.status == OrderStatus.DELIVERED
    assert order.rework_count == 0
    actions = [e.action for e in order.events.all()]
    assert actions[0] == EventAction.CREATED
    assert actions.count(EventAction.APPROVED) == 6
    assert actions.count(EventAction.READY_DISPATCH_SET) == 1


# ---- Reject ------------------------------------------------------------
@pytest.mark.parametrize("start", ["DESIGN", "FABRIC_PREP", "FABRIC_DONE", "STITCHING", "QA"])
def test_reject_routes(start):
    order = order_at(start)
    order = services.reject(order, "a", "bad")
    assert order.status == REJECT_TARGET[start]
    assert order.rework_count == 1
    event = order.events.last()
    assert event.action == EventAction.REJECTED
    assert event.data == {"from": start, "to": REJECT_TARGET[start]}
    assert event.note == "bad"


def test_reject_not_allowed_in_packaging():
    order = order_at("PACKAGING")
    with pytest.raises(DomainError) as e:
        services.reject(order, "a", "no")
    assert code_of(e) == "REJECT_NOT_ALLOWED"


def test_reject_not_allowed_when_delivered():
    order = services.set_ready_dispatch(order_at("PACKAGING"), "a", True, 1)
    order = services.approve(order, "a", tracking_number="T")
    with pytest.raises(DomainError) as e:
        services.reject(order, "a", "no")
    assert code_of(e) == "REJECT_NOT_ALLOWED"


@pytest.mark.parametrize("reason", ["", "   "])
def test_reject_requires_reason(reason):
    with pytest.raises(DomainError) as e:
        services.reject(make_order(), "a", reason)
    assert code_of(e) == "VALIDATION_ERROR"


def test_rework_count_accumulates():
    order = order_at("QA")
    order = services.reject(order, "a", "r1")        # QA -> STITCHING
    order = services.approve(order, "a", assembled_pieces_count=order.quantity)
    order = services.reject(order, "a", "r2")        # QA -> STITCHING
    assert order.rework_count == 2


# ---- Ready dispatch ----------------------------------------------------
def test_ready_dispatch_invalid_stage():
    with pytest.raises(DomainError) as e:
        services.set_ready_dispatch(make_order(), "a", True, 1)
    assert code_of(e) == "INVALID_STAGE"


@pytest.mark.parametrize("cartons", [None, 0])
def test_ready_dispatch_needs_cartons(cartons):
    with pytest.raises(DomainError) as e:
        services.set_ready_dispatch(order_at("PACKAGING"), "a", True, cartons)
    assert code_of(e) == "VALIDATION_ERROR"


def test_ready_dispatch_hold_and_ready():
    order = order_at("PACKAGING")
    order = services.set_ready_dispatch(order, "a", False)
    assert order.is_ready_dispatch is False
    order = services.set_ready_dispatch(order, "a", True, 3)
    assert order.is_ready_dispatch is True and order.cartons_count == 3
    assert order.events.last().action == EventAction.READY_DISPATCH_SET


# ---- Error status mapping ---------------------------------------------
def test_http_status_mapping():
    for code in ("ORDER_LOCKED", "INVALID_STAGE", "ORDER_COMPLETED", "REJECT_NOT_ALLOWED"):
        assert http_status_for(code) == 409
    assert http_status_for("QC_FAILED") == 400


# ---- SLA ---------------------------------------------------------------
@pytest.mark.parametrize("status,hours", [(s, h) for s, h in STAGE_SLA_HOURS.items() if h])
def test_sla_hours_table(status, hours):
    order = Order(status=status, stage_started_at=timezone.now())
    assert order.sla_hours == hours
    assert order.sla_deadline == order.stage_started_at + timedelta(hours=hours)


def test_is_overdue_after_deadline():
    with freeze_time("2026-01-01 00:00:00"):
        order = make_order()  # DESIGN, 27h
    with freeze_time("2026-01-02 02:59:00"):
        assert order.is_overdue is False
    with freeze_time("2026-01-02 03:01:00"):
        assert order.is_overdue is True


def test_delivered_never_overdue():
    order = Order(status=OrderStatus.DELIVERED, stage_started_at=timezone.now() - timedelta(days=999))
    assert order.is_overdue is False and order.sla_deadline is None and order.next_status is None


def test_stage_clock_resets_on_approve_and_reject():
    with freeze_time("2026-01-01 00:00:00"):
        order = make_order(pattern=make_pattern())
    with freeze_time("2026-01-01 10:00:00"):
        order = services.approve(order, "a")
        assert order.stage_started_at == timezone.now()
    with freeze_time("2026-01-01 20:00:00"):
        order = services.reject(order, "a", "again")  # FABRIC_PREP -> FABRIC_PREP
        assert order.status == OrderStatus.FABRIC_PREP
        assert order.stage_started_at == timezone.now()


def test_filter_overdue_queryset():
    with freeze_time("2026-01-01 00:00:00"):
        old = make_order(name="old")
    with freeze_time("2026-01-03 00:00:00"):
        fresh = make_order(name="fresh")
        assert list(services.filter_overdue(Order.objects.all(), True)) == [old]
        assert list(services.filter_overdue(Order.objects.all(), False)) == [fresh]


def test_next_status_table():
    assert make_order().next_status == NEXT_STATUS[OrderStatus.DESIGN]
