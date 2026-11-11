import pytest
from freezegun import freeze_time

from apps.orders.choices import OrderStatus
from conftest import make_color, make_inspection, make_order, make_pattern, order_at

pytestmark = pytest.mark.django_db

PAYLOAD = {
    "name": "Apron", "garment_type": "HEAT_INSULATION", "fabric_type": "COTTON",
    "requester_username": "somchai", "address": "Bangkok", "quantity": 10,
}


def assert_error(resp, status, code):
    assert resp.status_code == status, resp.content
    body = resp.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message", "details"}
    assert body["error"]["code"] == code


def test_health(api):
    assert api.get("/api/health/").json() == {"status": "ok"}


def test_fabric_rules(api):
    data = api.get("/api/fabric-rules/").json()
    assert "POLYESTER" not in data["HEAT_INSULATION"]
    assert set(data["WATERPROOF"]) == {"POLYESTER", "NYLON"}


def test_create_order_and_response_fields(api):
    resp = api.post("/api/orders/", PAYLOAD, format="json")
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "DESIGN"
    assert body["sla_hours"] == 27 and body["is_overdue"] is False
    assert body["next_status"] == "FABRIC_PREP" and body["sla_deadline"]
    assert body["pattern"] is None and body["rework_count"] == 0


def test_create_incompatible_fabric_400(api):
    resp = api.post("/api/orders/", {**PAYLOAD, "fabric_type": "POLYESTER"}, format="json")
    assert_error(resp, 400, "FABRIC_INCOMPATIBLE")
    assert "allowed_fabrics" in resp.json()["error"]["details"]


def test_create_validation_error_envelope(api):
    resp = api.post("/api/orders/", {**PAYLOAD, "quantity": 0, "name": ""}, format="json")
    assert_error(resp, 400, "VALIDATION_ERROR")
    assert "quantity" in resp.json()["error"]["details"]


def test_not_found_envelope(api):
    assert_error(api.get("/api/orders/999/"), 404, "NOT_FOUND")
    assert_error(api.post("/api/orders/999/approve/", {"actor": "a"}, format="json"), 404, "NOT_FOUND")


def test_put_disabled(api):
    order = make_order()
    assert api.put(f"/api/orders/{order.pk}/", PAYLOAD, format="json").status_code == 405


def test_patch_and_locked_409(api):
    order = make_order()
    resp = api.patch(f"/api/orders/{order.pk}/", {"name": "Renamed"}, format="json")
    assert resp.status_code == 200 and resp.json()["name"] == "Renamed"
    locked = order_at("FABRIC_PREP", name="locked")
    assert_error(api.patch(f"/api/orders/{locked.pk}/", {"name": "x"}, format="json"), 409, "ORDER_LOCKED")


def test_patch_cannot_change_status(api):
    order = make_order()
    api.patch(f"/api/orders/{order.pk}/", {"status": "QA"}, format="json")
    order.refresh_from_db()
    assert order.status == OrderStatus.DESIGN


def test_delete_and_locked(api):
    order = make_order()
    assert api.delete(f"/api/orders/{order.pk}/").status_code == 204
    locked = order_at("FABRIC_PREP")
    assert_error(api.delete(f"/api/orders/{locked.pk}/"), 409, "ORDER_LOCKED")


def test_approve_requires_actor(api):
    order = make_order()
    assert_error(api.post(f"/api/orders/{order.pk}/approve/", {}, format="json"), 400, "VALIDATION_ERROR")


def test_approve_pattern_required_then_ok(api):
    order = make_order()
    url = f"/api/orders/{order.pk}/approve/"
    assert_error(api.post(url, {"actor": "d"}, format="json"), 400, "PATTERN_REQUIRED")
    resp = api.post(url, {"actor": "d", "pattern_id": make_pattern().pk}, format="json")
    assert resp.status_code == 200 and resp.json()["status"] == "FABRIC_PREP"


def test_full_flow_via_api(api):
    insp = make_inspection()
    order = make_order(pattern=make_pattern(), quantity=4)
    base = f"/api/orders/{order.pk}"
    color = make_color()
    steps = [
        {"actor": "a"},
        {"actor": "a", "swatch_fabric_type": "COTTON", "measured_fabric_meters": "10.50"},
        {"actor": "a", "color_id": color.pk, "finished_fabric_meters": "9.75"},
        {"actor": "a", "assembled_pieces_count": 4},
        {"actor": "a", "results": [{"inspection_id": insp.pk, "passed": True}]},
    ]
    for body in steps:
        assert api.post(f"{base}/approve/", body, format="json").status_code == 200
    resp = api.post(f"{base}/ready-dispatch/", {"actor": "a", "is_ready": True, "cartons_count": 2}, format="json")
    assert resp.json()["is_ready_dispatch"] is True
    resp = api.post(f"{base}/approve/", {"actor": "a", "tracking_number": "TH1"}, format="json")
    assert resp.json()["status"] == "DELIVERED"
    assert_error(api.post(f"{base}/approve/", {"actor": "a"}, format="json"), 409, "ORDER_COMPLETED")
    events = api.get(f"{base}/events/").json()
    assert events[0]["action"] == "CREATED" and len(events) == 8


def test_reject_endpoint(api):
    order = order_at("QA")
    url = f"/api/orders/{order.pk}/reject/"
    assert_error(api.post(url, {"actor": "q"}, format="json"), 400, "VALIDATION_ERROR")
    resp = api.post(url, {"actor": "q", "reason": "bad seams"}, format="json")
    assert resp.json()["status"] == "STITCHING" and resp.json()["rework_count"] == 1


def test_reject_not_allowed_409(api):
    order = order_at("PACKAGING")
    resp = api.post(f"/api/orders/{order.pk}/reject/", {"actor": "q", "reason": "x"}, format="json")
    assert_error(resp, 409, "REJECT_NOT_ALLOWED")


def test_ready_dispatch_invalid_stage_409(api):
    order = make_order()
    resp = api.post(f"/api/orders/{order.pk}/ready-dispatch/", {"actor": "a", "is_ready": False}, format="json")
    assert_error(resp, 409, "INVALID_STAGE")


def test_ready_dispatch_needs_cartons_400(api):
    order = order_at("PACKAGING")
    resp = api.post(f"/api/orders/{order.pk}/ready-dispatch/", {"actor": "a", "is_ready": True}, format="json")
    assert_error(resp, 400, "VALIDATION_ERROR")


def test_not_ready_for_dispatch_400(api):
    order = order_at("PACKAGING")
    resp = api.post(f"/api/orders/{order.pk}/approve/", {"actor": "a", "tracking_number": "T"}, format="json")
    assert_error(resp, 400, "NOT_READY_FOR_DISPATCH")


# ---- list filters ------------------------------------------------------
def test_filters_and_search(api):
    make_order(name="Red apron", requester_username="alice")
    order_at("FABRIC_PREP", name="Blue shirt", requester_username="bob", garment_type="WINTER", fabric_type="WOOL")
    assert api.get("/api/orders/").json()["count"] == 2
    assert api.get("/api/orders/?status=DESIGN").json()["count"] == 1
    assert api.get("/api/orders/?garment_type=WINTER").json()["count"] == 1
    assert api.get("/api/orders/?search=alice").json()["results"][0]["name"] == "Red apron"
    assert api.get("/api/orders/?search=shirt").json()["count"] == 1


def test_overdue_filter(api):
    with freeze_time("2026-01-01 00:00:00"):
        make_order(name="stale")
    make_order(name="fresh")
    names = lambda q: [o["name"] for o in api.get(f"/api/orders/?overdue={q}").json()["results"]]
    assert names("true") == ["stale"]
    assert names("false") == ["fresh"]
    stale = api.get("/api/orders/?overdue=true").json()["results"][0]
    assert stale["is_overdue"] is True


def test_pagination_page_size(api):
    for i in range(21):
        make_order(name=f"o{i}")
    body = api.get("/api/orders/").json()
    assert body["count"] == 21 and len(body["results"]) == 20 and body["next"]
