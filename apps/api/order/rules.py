"""Pure rule helpers with no database access."""
from .choices import FabricType, GarmentType

ALL_FABRICS: list[str] = [f.value for f in FabricType]

# Which fabrics each garment type may use (R1).
FABRIC_COMPATIBILITY: dict[str, list[str]] = {
    GarmentType.GENERAL: ALL_FABRICS,
    GarmentType.HEAT_INSULATION: [FabricType.COTTON, FabricType.DENIM, FabricType.WOOL, FabricType.ARAMID],
    GarmentType.WATERPROOF: [FabricType.POLYESTER, FabricType.NYLON],
    GarmentType.WINTER: [FabricType.WOOL, FabricType.FLEECE, FabricType.DENIM, FabricType.POLYESTER],
    GarmentType.CHEAP: [FabricType.COTTON, FabricType.POLYESTER],
}


def allowed_fabrics(garment_type: str) -> list[str]:
    """Return the fabric values allowed for a garment type."""
    return [str(f) for f in FABRIC_COMPATIBILITY.get(garment_type, [])]


def is_fabric_allowed(garment_type: str, fabric_type: str) -> bool:
    """R1: True if this fabric may be used for this garment type."""
    return fabric_type in allowed_fabrics(garment_type)


def fabric_rules_table() -> dict[str, list[str]]:
    """The whole table as plain strings (used by GET /api/fabric-rules/)."""
    return {garment: allowed_fabrics(garment) for garment in FABRIC_COMPATIBILITY}
