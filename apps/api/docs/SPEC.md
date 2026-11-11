# SPEC — Garment Manufacturing Order Tracking API

Source of truth for implementation. Derived from the assignment Excalidraw
("Manufacturing process of garment process" + ER diagram).

## 1. Domain summary
A client places an **Order** for a garment. The order moves through 6 production
steps. Each step has an approve/reject gate and an SLA (time limit). Every
action is recorded as an **OrderEvent** (tracking timeline).

Key rule from the assignment note: *the garment type chosen at step 1 constrains
later steps* — e.g. a kitchen apron (HEAT_INSULATION) must NOT use polyester,
because polyester is not heat-resistant.

## 2. Enums (`apps/orders/choices.py`)
- `GarmentType`: GENERAL, HEAT_INSULATION, WATERPROOF, WINTER, CHEAP
- `FabricType`: COTTON, LINEN, DENIM, WOOL, FLEECE, POLYESTER, NYLON, ARAMID
- `OrderStatus` (ordered): DESIGN, FABRIC_PREP, FABRIC_DONE, STITCHING, QA, PACKAGING, DELIVERED
- `EventAction`: CREATED, APPROVED, REJECTED, READY_DISPATCH_SET, UPDATED
- `PatternType` (catalog): APRON, SHIRT, PANTS, JACKET, DRESS, OTHER

## 3. Fabric compatibility (`apps/orders/rules.py`)
| GarmentType | Allowed fabrics |
|---|---|
| GENERAL | all |
| HEAT_INSULATION | COTTON, DENIM, WOOL, ARAMID |
| WATERPROOF | POLYESTER, NYLON |
| WINTER | WOOL, FLEECE, DENIM, POLYESTER |
| CHEAP | COTTON, POLYESTER |

Expose `is_fabric_allowed(garment_type, fabric_type) -> bool` and the table via
`GET /api/fabric-rules/`.

## 4. Status ↔ diagram step, SLA, reject target
| Status | Diagram step | Sub-tasks (SLA) | Stage SLA | Reject goes to |
|---|---|---|---|---|
| DESIGN | 1 Design & Pattern cutting | Designer 24h + Machine 3h | 27h | DESIGN (back to designer) |
| FABRIC_PREP | 2 Fabric sourcing & prep | Procurement 24h + Measure 12h | 36h | FABRIC_PREP (re-source swatches) |
| FABRIC_DONE | 3 Fabric finishing | Combine 12h + Dyeing 48h | 60h | FABRIC_PREP (workpiece rejected → step 2) |
| STITCHING | 4 Assembly & Stitching | Assembly 48h | 48h | STITCHING (re-stitch) |
| QA | 5 QA & Inspection | QA 12h | 12h | STITCHING (fails QC → step 4) |
| PACKAGING | 6 Packaging & Delivery | Packaging 24h | 24h | — (no reject; use ready-dispatch=false = hold in staging) |
| DELIVERED | terminal | — | — | — |

Order stores `stage_started_at` (reset on every status change, incl. reject to
same status). Computed: `sla_deadline = stage_started_at + stage SLA`,
`is_overdue = now > sla_deadline` (False when DELIVERED).
Order stores `rework_count` (+1 on every reject).

## 5. Models
### catalog app
- `Pattern`: name, pattern_type (PatternType), piece_count (int ≥1, "amount of piece"), pattern_metric (JSON, e.g. {"length_cm": 80}), timestamps
- `Color`: name, code (unique, `#RRGGBB` validated, stored uppercase), timestamps
- `Inspection` (QA checklist item per garment type): name, garment_type, description (blank ok), timestamps

### orders app
- `Order`: name, garment_type, fabric_type, requester_username ("username req"), address,
  quantity (int ≥1), pattern FK→Pattern (nullable, PROTECT), color FK→Color (nullable, PROTECT),
  color_metric (JSON, default {} — dye spec), status (default DESIGN), is_ready_dispatch (bool, default False),
  measured_fabric_meters (Decimal, null), finished_fabric_meters (Decimal, null),
  assembled_pieces_count (int, null), cartons_count (int, null), tracking_number (str, blank),
  rework_count (int, 0), stage_started_at, created_at, updated_at. Ordering: -created_at.
- `OrderEvent`: order FK (related_name="events", CASCADE), status (stage when it happened), action,
  actor (str), note (text blank), data (JSON default {}), created_at. Ordering: created_at.

## 6. Business rules (all in `apps/orders/services.py`, raise `DomainError`)
Create order:
- R1 fabric must be allowed for garment type → `FABRIC_INCOMPATIBLE`
- Creates CREATED event, status=DESIGN.

Update order (PATCH name/address/quantity/pattern/color/color_metric/fabric_type/garment_type):
- R2 only while DESIGN → `ORDER_LOCKED`; re-check R1 on garment/fabric change. Logs UPDATED.
Delete order:
- R3 only while DESIGN → `ORDER_LOCKED`.

`approve(order, actor, note, **data)` — gate per current status, then advance to next status:
- DESIGN: order.pattern required (may be supplied as `pattern_id`) → `PATTERN_REQUIRED`
- FABRIC_PREP: `swatch_fabric_type` required & must equal order.fabric_type → `SWATCH_MISMATCH`;
  also must be allowed (R1) → `FABRIC_INCOMPATIBLE`; `measured_fabric_meters` > 0 required → `VALIDATION_ERROR`. Store meters.
- FABRIC_DONE: order.color required (may be supplied as `color_id`) → `COLOR_REQUIRED`;
  `finished_fabric_meters` > 0 and ≤ measured_fabric_meters → `YIELD_EXCEEDS_MEASURED`. Store.
- STITCHING: `assembled_pieces_count` == order.quantity → `PIECE_COUNT_MISMATCH`. Store.
- QA: `results` = list of {inspection_id, passed}. Must contain every Inspection for the order's
  garment_type → `INSPECTION_INCOMPLETE`; all passed → `QC_FAILED` (caller should reject instead).
  If no Inspection exists for the garment type, approval allowed. Results saved in event data.
- PACKAGING: is_ready_dispatch must be True → `NOT_READY_FOR_DISPATCH`; `tracking_number` required. Store → DELIVERED.
- DELIVERED: → `ORDER_COMPLETED`.
Logs APPROVED event (data = submitted payload, status = stage approved).

`reject(order, actor, reason)` — reason required. Moves to reject target (table §4), rework_count+1,
logs REJECTED (data: {"from": X, "to": Y}). PACKAGING/DELIVERED → `REJECT_NOT_ALLOWED`.

`set_ready_dispatch(order, actor, is_ready, cartons_count=None)` — only in PACKAGING → `INVALID_STAGE`.
is_ready=True requires cartons_count ≥1. Logs READY_DISPATCH_SET. (False = "hold in finished goods staging area".)

All state changes inside `transaction.atomic()` with `select_for_update()` on the order.

## 7. API (DRF, prefix `/api/`)
| Method | Path | Notes |
|---|---|---|
| GET | /api/health/ | {"status":"ok"} |
| CRUD | /api/patterns/ | ModelViewSet |
| CRUD | /api/colors/ | ModelViewSet |
| CRUD | /api/inspections/ | ModelViewSet, filter `?garment_type=` |
| GET | /api/fabric-rules/ | compatibility table |
| GET/POST | /api/orders/ | list filters: `status`, `garment_type`, `overdue=true` ; search `?search=` on name/requester_username |
| GET/PATCH/DELETE | /api/orders/{id}/ | PUT disabled |
| POST | /api/orders/{id}/approve/ | body: actor, note, + stage fields |
| POST | /api/orders/{id}/reject/ | body: actor, reason |
| POST | /api/orders/{id}/ready-dispatch/ | body: actor, is_ready, cartons_count |
| GET | /api/orders/{id}/events/ | timeline |
| GET | /api/schema/ , /api/docs/ | drf-spectacular OpenAPI + Swagger UI |

Order response includes: all fields, `pattern`/`color` ids, `sla_hours`, `sla_deadline`, `is_overdue`, `next_status`.
Pagination: PageNumberPagination, page_size 20.
Auth: none (AllowAny) — `actor` string identifies who acted. Documented as a deliberate simplification.

Error envelope (custom exception handler) for DomainError and DRF errors:
`{"error": {"code": "FABRIC_INCOMPATIBLE", "message": "...", "details": {...}}}`
DomainError → 400 (ORDER_LOCKED / INVALID_STAGE / ORDER_COMPLETED / REJECT_NOT_ALLOWED → 409). 404 → code NOT_FOUND. Validation → VALIDATION_ERROR.

Implementation notes (decided during build):
- Deleting a Pattern/Color still referenced by an order → 409 `IN_USE`.
- POST/PATCH /api/orders/ accept optional write-only `actor` (defaults to requester_username).
- Missing tracking_number, non-positive meters, empty reject reason, unknown pattern/color/inspection id,
  cartons_count < 1 → `VALIDATION_ERROR`. Missing swatch_fabric_type → `SWATCH_MISMATCH`.
- In the service, `REJECT_NOT_ALLOWED` is checked before the reason; via the API a missing `reason`
  field fails serializer validation first (400 `VALIDATION_ERROR`). `overdue` filter is computed in SQL.
