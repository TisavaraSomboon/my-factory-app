import pytest

from apps.orders.choices import FabricType, GarmentType
from apps.orders.rules import fabric_rules_table, is_fabric_allowed


def test_general_allows_every_fabric():
    assert all(is_fabric_allowed(GarmentType.GENERAL, f) for f in FabricType.values)


def test_heat_insulation_rejects_polyester():
    assert not is_fabric_allowed(GarmentType.HEAT_INSULATION, FabricType.POLYESTER)


@pytest.mark.parametrize("fabric", ["COTTON", "DENIM", "WOOL", "ARAMID"])
def test_heat_insulation_allowed(fabric):
    assert is_fabric_allowed("HEAT_INSULATION", fabric)


@pytest.mark.parametrize("garment,fabric,expected", [
    ("WATERPROOF", "NYLON", True), ("WATERPROOF", "COTTON", False),
    ("WINTER", "FLEECE", True), ("WINTER", "LINEN", False),
    ("CHEAP", "COTTON", True), ("CHEAP", "WOOL", False),
])
def test_table_rows(garment, fabric, expected):
    assert is_fabric_allowed(garment, fabric) is expected


def test_table_lists_all_garment_types_as_strings():
    table = fabric_rules_table()
    assert set(table) == set(GarmentType.values)
    assert all(isinstance(f, str) for fabrics in table.values() for f in fabrics)
