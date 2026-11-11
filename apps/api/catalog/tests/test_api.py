import pytest

from apps.catalog.models import Color
from conftest import make_color, make_inspection, make_pattern

pytestmark = pytest.mark.django_db


def test_pattern_crud(api):
    body = {"name": "Shirt", "pattern_type": "SHIRT", "piece_count": 5, "pattern_metric": {"chest_cm": 100}}
    created = api.post("/api/patterns/", body, format="json")
    assert created.status_code == 201
    pid = created.json()["id"]
    assert api.get(f"/api/patterns/{pid}/").json()["pattern_metric"] == {"chest_cm": 100}
    assert api.patch(f"/api/patterns/{pid}/", {"piece_count": 6}, format="json").json()["piece_count"] == 6
    assert api.get("/api/patterns/").json()["count"] == 1
    assert api.delete(f"/api/patterns/{pid}/").status_code == 204


def test_pattern_piece_count_min_1(api):
    body = {"name": "X", "pattern_type": "SHIRT", "piece_count": 0}
    resp = api.post("/api/patterns/", body, format="json")
    assert resp.status_code == 400 and resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_pattern_invalid_type(api):
    resp = api.post("/api/patterns/", {"name": "X", "pattern_type": "HAT", "piece_count": 1}, format="json")
    assert resp.status_code == 400


def test_color_crud_uppercases_code(api):
    created = api.post("/api/colors/", {"name": "Teal", "code": "#00aabb"}, format="json")
    assert created.status_code == 201 and created.json()["code"] == "#00AABB"
    cid = created.json()["id"]
    assert api.patch(f"/api/colors/{cid}/", {"name": "Teal 2"}, format="json").status_code == 200
    assert api.delete(f"/api/colors/{cid}/").status_code == 204


@pytest.mark.parametrize("code", ["00AABB", "#00AAB", "#GGGGGG", "#00AABBCC", "red"])
def test_color_code_invalid(api, code):
    resp = api.post("/api/colors/", {"name": "Bad", "code": code}, format="json")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "code" in resp.json()["error"]["details"]


def test_color_code_unique_case_insensitive(api):
    make_color("#ABCDEF")
    resp = api.post("/api/colors/", {"name": "Dup", "code": "#abcdef"}, format="json")
    assert resp.status_code == 400
    assert Color.objects.count() == 1


def test_color_update_same_code_ok(api):
    color = make_color("#ABCDEF")
    resp = api.patch(f"/api/colors/{color.pk}/", {"code": "#abcdef"}, format="json")
    assert resp.status_code == 200


def test_inspection_crud_and_filter(api):
    make_inspection("WINTER", "Warmth")
    make_inspection("CHEAP", "Look")
    assert api.get("/api/inspections/").json()["count"] == 2
    filtered = api.get("/api/inspections/?garment_type=WINTER").json()
    assert filtered["count"] == 1 and filtered["results"][0]["name"] == "Warmth"
    created = api.post("/api/inspections/", {"name": "N", "garment_type": "GENERAL"}, format="json")
    assert created.status_code == 201 and created.json()["description"] == ""
    assert api.delete(f"/api/inspections/{created.json()['id']}/").status_code == 204


def test_delete_pattern_in_use_is_protected(api):
    from conftest import make_order
    pattern = make_pattern()
    make_order(pattern=pattern)
    resp = api.delete(f"/api/patterns/{pattern.pk}/")
    assert resp.status_code == 409 and resp.json()["error"]["code"] == "IN_USE"
