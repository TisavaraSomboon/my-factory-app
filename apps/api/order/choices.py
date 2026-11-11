"""Enums and the workflow tables (transitions, reject targets, SLAs)."""
from django.db import models


class GarmentType(models.TextChoices):
    GENERAL = "GENERAL"
    HEAT_INSULATION = "HEAT_INSULATION"
    WATERPROOF = "WATERPROOF"
    WINTER = "WINTER"
    CHEAP = "CHEAP"


class FabricType(models.TextChoices):
    COTTON = "COTTON"
    LINEN = "LINEN"
    DENIM = "DENIM"
    WOOL = "WOOL"
    FLEECE = "FLEECE"
    POLYESTER = "POLYESTER"
    NYLON = "NYLON"
    ARAMID = "ARAMID"


class OrderStatus(models.TextChoices):
    DESIGN = "DESIGN"
    FABRIC_PREP = "FABRIC_PREP"
    FABRIC_DONE = "FABRIC_DONE"
    STITCHING = "STITCHING"
    QA = "QA"
    PACKAGING = "PACKAGING"
    DELIVERED = "DELIVERED"


class EventAction(models.TextChoices):
    CREATED = "CREATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    READY_DISPATCH_SET = "READY_DISPATCH_SET"
    UPDATED = "UPDATED"


# Where an approval moves the order (section 4 of the spec).
NEXT_STATUS: dict[str, str | None] = {
    OrderStatus.DESIGN: OrderStatus.FABRIC_PREP,
    OrderStatus.FABRIC_PREP: OrderStatus.FABRIC_DONE,
    OrderStatus.FABRIC_DONE: OrderStatus.STITCHING,
    OrderStatus.STITCHING: OrderStatus.QA,
    OrderStatus.QA: OrderStatus.PACKAGING,
    OrderStatus.PACKAGING: OrderStatus.DELIVERED,
    OrderStatus.DELIVERED: None,
}

# Where a rejection sends the order. PACKAGING/DELIVERED cannot be rejected.
REJECT_TARGET: dict[str, str | None] = {
    OrderStatus.DESIGN: OrderStatus.DESIGN,
    OrderStatus.FABRIC_PREP: OrderStatus.FABRIC_PREP,
    OrderStatus.FABRIC_DONE: OrderStatus.FABRIC_PREP,
    OrderStatus.STITCHING: OrderStatus.STITCHING,
    OrderStatus.QA: OrderStatus.STITCHING,
    OrderStatus.PACKAGING: None,
    OrderStatus.DELIVERED: None,
}

# Time limit per stage, in hours (sum of the sub-task SLAs). DELIVERED has none.
STAGE_SLA_HOURS: dict[str, int | None] = {
    OrderStatus.DESIGN: 27,
    OrderStatus.FABRIC_PREP: 36,
    OrderStatus.FABRIC_DONE: 60,
    OrderStatus.STITCHING: 48,
    OrderStatus.QA: 12,
    OrderStatus.PACKAGING: 24,
    OrderStatus.DELIVERED: None,
}
