# API Reference

Interactive docs: Swagger UI at `/api/docs/`, OpenAPI schema at `/api/schema/`. This page explains the same API in plain language. For the rules behind the errors see [BUSINESS_LOGIC.md](BUSINESS_LOGIC.md).

## Conventions

- **Base URL:** `http://localhost:8000/api/`
- **Format:** JSON in and out. Send `Content-Type: application/json`.
- **Auth:** none. Write calls carry an `actor` string (who did it); it is recorded in the order timeline.
- **Timestamps:** ISO 8601 with timezone. **Decimals** (meters) are returned as strings, e.g. `"25.50"`.
- **Pagination** (all list endpoints except `/orders/{id}/events/` and `/fabric-rules/`): page size 20, use `?page=2`.

```json
{"count": 2, "next": null, "previous": null, "results": [ ... ]}
```

- **Error envelope** (every error, always the same shape):

```json
{"error": {"code": "FABRIC_INCOMPATIBLE", "message": "Human readable text", "details": {}}}
```

`details` is an object with extra info (it can be empty). For `VALIDATION_ERROR` it maps field names to lists of messages.

### HTTP status and error codes

| HTTP | Code | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Missing/invalid field, unknown pattern/color/inspection id, non-positive meters, empty reject reason, `cartons_count` < 1, missing `tracking_number` |
| 400 | `FABRIC_INCOMPATIBLE` | Fabric not allowed for the garment type (create, update, FABRIC_PREP) |
| 400 | `PATTERN_REQUIRED` | Approving DESIGN without a pattern |
| 400 | `SWATCH_MISMATCH` | Swatch missing or different from the order's fabric |
| 400 | `COLOR_REQUIRED` | Approving FABRIC_DONE without a color |
| 400 | `YIELD_EXCEEDS_MEASURED` | Finished meters greater than measured meters |
| 400 | `PIECE_COUNT_MISMATCH` | Assembled pieces differ from the order quantity |
| 400 | `INSPECTION_INCOMPLETE` | QA results do not cover every inspection of the garment type |
| 400 | `QC_FAILED` | At least one QA inspection failed (reject the order instead) |
| 400 | `NOT_READY_FOR_DISPATCH` | Approving PACKAGING while `is_ready_dispatch` is false |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `ORDER_LOCKED` | Edit/delete an order that is no longer in DESIGN |
| 409 | `INVALID_STAGE` | `ready-dispatch` when the order is not in PACKAGING |
| 409 | `ORDER_COMPLETED` | Approving an order that is already DELIVERED |
| 409 | `REJECT_NOT_ALLOWED` | Rejecting an order in PACKAGING or DELIVERED |
| 409 | `IN_USE` | Deleting a Pattern/Color that an order still references |

## Enums

| Enum | Values |
|---|---|
| `garment_type` | `GENERAL`, `HEAT_INSULATION`, `WATERPROOF`, `WINTER`, `CHEAP` |
| `fabric_type` | `COTTON`, `LINEN`, `DENIM`, `WOOL`, `FLEECE`, `POLYESTER`, `NYLON`, `ARAMID` |
| `status` | `DESIGN`, `FABRIC_PREP`, `FABRIC_DONE`, `STITCHING`, `QA`, `PACKAGING`, `DELIVERED` |
| event `action` | `CREATED`, `APPROVED`, `REJECTED`, `READY_DISPATCH_SET`, `UPDATED` |
| `pattern_type` | `APRON`, `SHIRT`, `PANTS`, `JACKET`, `DRESS`, `OTHER` |

## Order response fields

| Field | Type | Notes |
|---|---|---|
| `id` | int | |
| `name` | string | |
| `garment_type` | enum | |
| `fabric_type` | enum | |
| `requester_username` | string | The customer who requested the order |
| `address` | string | Delivery address |
| `quantity` | int | >= 1 |
| `pattern` | int or null | Pattern id |
| `color` | int or null | Color id |
| `color_metric` | object | Free-form dye spec, default `{}` |
| `status` | enum | Read-only. Changed only by approve/reject |
| `is_ready_dispatch` | bool | Read-only. Set via `/ready-dispatch/` |
| `measured_fabric_meters` | string or null | Stored at FABRIC_PREP approval |
| `finished_fabric_meters` | string or null | Stored at FABRIC_DONE approval |
| `assembled_pieces_count` | int or null | Stored at STITCHING approval |
| `cartons_count` | int or null | Stored by `/ready-dispatch/` with `is_ready=true` |
| `tracking_number` | string | Empty until PACKAGING is approved |
| `rework_count` | int | +1 on every reject |
| `stage_started_at` | datetime | Restarts on every status change (including reject to the same status) |
| `created_at`, `updated_at` | datetime | |
| `sla_hours` | int or null | Time limit of the current stage; `null` when DELIVERED |
| `sla_deadline` | datetime or null | `stage_started_at + sla_hours`; `null` when DELIVERED |
| `is_overdue` | bool | `now > sla_deadline`; always `false` when DELIVERED |
| `next_status` | enum or null | Where approve would move the order; `null` when DELIVERED |

`actor` is a write-only field on create/update and does not appear in responses.

---

## Health

### GET /api/health/
Liveness check.
```bash
curl -s localhost:8000/api/health/
```
```json
{"status": "ok"}
```

## Fabric rules

### GET /api/fabric-rules/
Returns the garment type to allowed fabrics table (not paginated).
```bash
curl -s localhost:8000/api/fabric-rules/
```
```json
{"GENERAL": ["COTTON", "LINEN", "DENIM", "WOOL", "FLEECE", "POLYESTER", "NYLON", "ARAMID"],
 "HEAT_INSULATION": ["COTTON", "DENIM", "WOOL", "ARAMID"],
 "WATERPROOF": ["POLYESTER", "NYLON"],
 "WINTER": ["WOOL", "FLEECE", "DENIM", "POLYESTER"],
 "CHEAP": ["COTTON", "POLYESTER"]}
```

---

## Orders

### POST /api/orders/
Create an order. Status starts at `DESIGN`. Checks fabric compatibility (rule R1) and logs a `CREATED` event.

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | |
| `garment_type` | enum | yes | |
| `fabric_type` | enum | yes | Must be allowed for the garment type |
| `requester_username` | string | yes | |
| `address` | string | yes | |
| `quantity` | int | yes | >= 1 |
| `pattern` | int | no | Pattern id |
| `color` | int | no | Color id |
| `color_metric` | object | no | Default `{}` |
| `actor` | string | no | Defaults to `requester_username` |

```bash
curl -s -X POST localhost:8000/api/orders/ -H 'Content-Type: application/json' -d '{
  "name": "Kitchen apron", "garment_type": "HEAT_INSULATION", "fabric_type": "COTTON",
  "requester_username": "somchai", "address": "1 Sukhumvit Rd, Bangkok", "quantity": 10}'
```
Response `201`:
```json
{"id": 7, "name": "Kitchen apron", "garment_type": "HEAT_INSULATION", "fabric_type": "COTTON",
 "requester_username": "somchai", "address": "1 Sukhumvit Rd, Bangkok", "quantity": 10,
 "pattern": null, "color": null, "color_metric": {}, "status": "DESIGN", "is_ready_dispatch": false,
 "measured_fabric_meters": null, "finished_fabric_meters": null, "assembled_pieces_count": null,
 "cartons_count": null, "tracking_number": "", "rework_count": 0,
 "stage_started_at": "2026-11-09T22:33:09.302210+07:00", "created_at": "2026-11-09T22:33:09.302637+07:00",
 "updated_at": "2026-11-09T22:33:09.302648+07:00", "sla_hours": 27,
 "sla_deadline": "2026-11-11T01:33:09.302210+07:00", "is_overdue": false, "next_status": "FABRIC_PREP"}
```
Errors: `400 FABRIC_INCOMPATIBLE` (e.g. POLYESTER + HEAT_INSULATION), `400 VALIDATION_ERROR` (missing fields, `quantity` < 1).

```json
{"error": {"code": "FABRIC_INCOMPATIBLE", "message": "POLYESTER cannot be used for HEAT_INSULATION garments.",
  "details": {"garment_type": "HEAT_INSULATION", "fabric_type": "POLYESTER",
              "allowed_fabrics": ["COTTON", "DENIM", "WOOL", "ARAMID"]}}}
```

### GET /api/orders/
List orders, newest first, paginated.

| Query param | Notes |
|---|---|
| `status` | Exact status, e.g. `?status=QA` |
| `garment_type` | Exact garment type |
| `overdue` | `true` = past SLA deadline, `false` = not overdue |
| `search` | Matches `name` and `requester_username` (partial) |
| `page` | Page number |

```bash
curl -s "localhost:8000/api/orders/?status=DELIVERED&search=apron"
```
```json
{"count": 1, "next": null, "previous": null, "results": [ {"id": 7, "status": "DELIVERED", "...": "..."} ]}
```

### GET /api/orders/{id}/
Returns one order (same shape as above). Errors: `404 NOT_FOUND`.

### PATCH /api/orders/{id}/
Edit an order. Only allowed while status is `DESIGN` (rule R2). `PUT` is disabled (405). If `garment_type` or `fabric_type` changes, the compatibility check runs again. Logs an `UPDATED` event.

Body fields (all optional): `name`, `address`, `quantity`, `pattern`, `color`, `color_metric`, `fabric_type`, `garment_type`, `actor`. Other fields (such as `status`) are read-only and ignored.

```bash
curl -s -X PATCH localhost:8000/api/orders/7/ -H 'Content-Type: application/json' -d '{"quantity": 12}'
```
Errors: `409 ORDER_LOCKED` (`details: {"status": "DELIVERED"}`), `400 FABRIC_INCOMPATIBLE`, `400 VALIDATION_ERROR`, `404 NOT_FOUND`.

### DELETE /api/orders/{id}/
Delete an order. Only allowed while status is `DESIGN` (rule R3). Response `204` with no body. Errors: `409 ORDER_LOCKED`, `404 NOT_FOUND`.

### GET /api/orders/{id}/events/
The order timeline, oldest first. Not paginated.

| Event field | Notes |
|---|---|
| `id`, `order` | Event id and order id |
| `status` | The stage the order was in when the action happened |
| `action` | `CREATED`, `APPROVED`, `REJECTED`, `READY_DISPATCH_SET`, `UPDATED` |
| `actor` | Who did it |
| `note` | Approve note, or the reject reason |
| `data` | Submitted payload (approve), `{"from","to"}` (reject), `{"is_ready","cartons_count"}` (ready-dispatch), changed fields (update) |
| `created_at` | |

```bash
curl -s localhost:8000/api/orders/7/events/
```
```json
[{"id": 32, "order": 7, "status": "QA", "action": "REJECTED", "actor": "qa1",
  "note": "Loose stitching on seams", "data": {"from": "QA", "to": "STITCHING"},
  "created_at": "2026-11-09T22:33:09.454809+07:00"}]
```

### POST /api/orders/{id}/reject/
Reject the current stage. The order moves to the reject target and `rework_count` increases by 1.

| Current status | Moves to |
|---|---|
| DESIGN | DESIGN |
| FABRIC_PREP | FABRIC_PREP |
| FABRIC_DONE | FABRIC_PREP |
| STITCHING | STITCHING |
| QA | STITCHING |
| PACKAGING, DELIVERED | not allowed |

| Field | Type | Required | Notes |
|---|---|---|---|
| `actor` | string | yes | |
| `reason` | string | yes | Not blank. Saved as the event `note` |

```bash
curl -s -X POST localhost:8000/api/orders/7/reject/ -H 'Content-Type: application/json' \
  -d '{"actor": "qa1", "reason": "Loose stitching on seams"}'
```
Response `200`: the updated order (`"status": "STITCHING"`, `"rework_count": 1`).

Errors: `409 REJECT_NOT_ALLOWED` (PACKAGING/DELIVERED), `400 VALIDATION_ERROR` (missing actor/reason), `404 NOT_FOUND`.
```json
{"error": {"code": "REJECT_NOT_ALLOWED", "message": "Orders in DELIVERED cannot be rejected.", "details": {"status": "DELIVERED"}}}
```

### POST /api/orders/{id}/ready-dispatch/
Only while status is `PACKAGING`. `is_ready=true` marks the order ready (needs `cartons_count`); `is_ready=false` means "hold in the finished goods staging area". Logs `READY_DISPATCH_SET`. The status does not change.

| Field | Type | Required | Notes |
|---|---|---|---|
| `actor` | string | yes | |
| `is_ready` | bool | yes | |
| `cartons_count` | int | when `is_ready` is true | >= 1 |

```bash
curl -s -X POST localhost:8000/api/orders/7/ready-dispatch/ -H 'Content-Type: application/json' \
  -d '{"actor": "packer1", "is_ready": true, "cartons_count": 3}'
```
Response `200`: the order with `"is_ready_dispatch": true, "cartons_count": 3`.

Errors: `409 INVALID_STAGE` (`details: {"status": "DESIGN"}`), `400 VALIDATION_ERROR` (`cartons_count` missing when ready, or < 1), `404 NOT_FOUND`.

### POST /api/orders/{id}/approve/
Approve the current stage and move the order to the next status. Common body fields:

| Field | Type | Required | Notes |
|---|---|---|---|
| `actor` | string | yes | Missing actor gives `400 VALIDATION_ERROR` |
| `note` | string | no | Saved on the event |

Which extra fields are needed depends on the **current** status. The response is always `200` with the updated order. On any error the order does not change. Approving a `DELIVERED` order returns `409 ORDER_COMPLETED`.

#### Stage DESIGN (to FABRIC_PREP)
| Field | Type | Required | Notes |
|---|---|---|---|
| `pattern_id` | int | if the order has no pattern yet | Attaches this pattern to the order |

Errors: `400 PATTERN_REQUIRED` (no pattern on order and no `pattern_id`), `400 VALIDATION_ERROR` (`pattern_id` does not exist).
```bash
curl -s -X POST localhost:8000/api/orders/7/approve/ -H 'Content-Type: application/json' -d '{"actor": "designer1", "pattern_id": 1}'
```
```json
{"id": 7, "pattern": 1, "status": "FABRIC_PREP", "sla_hours": 36, "next_status": "FABRIC_DONE", "...": "..."}
```

#### Stage FABRIC_PREP (to FABRIC_DONE)
| Field | Type | Required | Notes |
|---|---|---|---|
| `swatch_fabric_type` | enum | yes | Must equal the order's `fabric_type` |
| `measured_fabric_meters` | decimal | yes | > 0, up to 2 decimal places. Stored on the order |

Errors: `400 SWATCH_MISMATCH` (missing or different), `400 FABRIC_INCOMPATIBLE` (swatch not allowed for the garment), `400 VALIDATION_ERROR` (meters missing or <= 0; invalid enum value).
```bash
curl -s -X POST localhost:8000/api/orders/7/approve/ -H 'Content-Type: application/json' \
  -d '{"actor": "buyer1", "swatch_fabric_type": "COTTON", "measured_fabric_meters": "25.50"}'
```
```json
{"status": "FABRIC_DONE", "measured_fabric_meters": "25.50", "sla_hours": 60, "...": "..."}
```

#### Stage FABRIC_DONE (to STITCHING)
| Field | Type | Required | Notes |
|---|---|---|---|
| `color_id` | int | if the order has no color yet | Attaches this color |
| `finished_fabric_meters` | decimal | yes | > 0 and <= `measured_fabric_meters` |

Errors: `400 COLOR_REQUIRED`, `400 YIELD_EXCEEDS_MEASURED`, `400 VALIDATION_ERROR` (unknown `color_id`, meters missing or <= 0).
```bash
curl -s -X POST localhost:8000/api/orders/7/approve/ -H 'Content-Type: application/json' \
  -d '{"actor": "dyer1", "color_id": 1, "finished_fabric_meters": "30"}'
```
```json
{"error": {"code": "YIELD_EXCEEDS_MEASURED", "message": "Finished fabric cannot exceed measured fabric.",
  "details": {"finished_fabric_meters": "30.00", "measured_fabric_meters": "25.50"}}}
```

#### Stage STITCHING (to QA)
| Field | Type | Required | Notes |
|---|---|---|---|
| `assembled_pieces_count` | int | yes | Must equal the order `quantity` |

Errors: `400 PIECE_COUNT_MISMATCH` (`details: {"assembled_pieces_count", "quantity"}`).
```bash
curl -s -X POST localhost:8000/api/orders/7/approve/ -H 'Content-Type: application/json' -d '{"actor": "sewer1", "assembled_pieces_count": 10}'
```
```json
{"status": "QA", "assembled_pieces_count": 10, "sla_hours": 12, "...": "..."}
```

#### Stage QA (to PACKAGING)
| Field | Type | Required | Notes |
|---|---|---|---|
| `results` | list | yes when the garment type has inspections | Items: `{"inspection_id": int, "passed": bool}` |

Every inspection defined for the order's garment type must appear, and all must have `passed: true`. If the garment type has no inspections, approval needs no results. The results are saved in the event `data`.

Errors: `400 INSPECTION_INCOMPLETE` (`details.missing_inspection_ids`), `400 QC_FAILED` (`details.failed_inspection_ids`; call `/reject/` instead), `400 VALIDATION_ERROR` (an id that does not belong to this garment type).
```bash
curl -s -X POST localhost:8000/api/orders/7/approve/ -H 'Content-Type: application/json' \
  -d '{"actor": "qa1", "results": [{"inspection_id": 3, "passed": true}]}'
```
```json
{"error": {"code": "INSPECTION_INCOMPLETE", "message": "Every inspection for this garment type must be answered.",
  "details": {"missing_inspection_ids": [4]}}}
```

#### Stage PACKAGING (to DELIVERED)
| Field | Type | Required | Notes |
|---|---|---|---|
| `tracking_number` | string | yes | Not blank. Stored on the order |

The order must already be marked ready via `/ready-dispatch/`.

Errors: `400 NOT_READY_FOR_DISPATCH`, `400 VALIDATION_ERROR` (blank tracking number).
```bash
curl -s -X POST localhost:8000/api/orders/7/approve/ -H 'Content-Type: application/json' -d '{"actor": "packer1", "tracking_number": "TH123456789"}'
```
```json
{"status": "DELIVERED", "tracking_number": "TH123456789", "sla_hours": null, "sla_deadline": null, "is_overdue": false, "next_status": null, "...": "..."}
```

#### Stage DELIVERED
Always fails with `409 ORDER_COMPLETED`.

---

## Catalog

Plain CRUD (`GET` list, `POST`, `GET {id}`, `PUT`, `PATCH`, `DELETE`), paginated.

### /api/patterns/
| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | int | read-only | |
| `name` | string | yes | max 120 chars |
| `pattern_type` | enum | yes | `APRON`, `SHIRT`, `PANTS`, `JACKET`, `DRESS`, `OTHER` |
| `piece_count` | int | yes | >= 1 (amount of pieces) |
| `pattern_metric` | object | no | e.g. `{"length_cm": 80}` |
| `created_at`, `updated_at` | datetime | read-only | |

Query params: `pattern_type`, `search` (name).
```bash
curl -s -X POST localhost:8000/api/patterns/ -H 'Content-Type: application/json' \
  -d '{"name": "Kitchen apron", "pattern_type": "APRON", "piece_count": 3, "pattern_metric": {"length_cm": 80, "width_cm": 60}}'
```
```json
{"id": 1, "name": "Kitchen apron", "pattern_type": "APRON", "piece_count": 3,
 "pattern_metric": {"length_cm": 80, "width_cm": 60}, "created_at": "...", "updated_at": "..."}
```
`DELETE` returns `409 IN_USE` if an order still references the pattern:
```json
{"error": {"code": "IN_USE", "message": "Cannot delete: still referenced by orders.", "details": {}}}
```

### /api/colors/
| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | int | read-only | |
| `name` | string | yes | max 60 chars |
| `code` | string | yes | `#RRGGBB` (6 hex digits). Stored uppercase; unique ignoring case |
| `created_at`, `updated_at` | datetime | read-only | |

Query params: `search` (name or code). `DELETE` returns `409 IN_USE` when still used by an order.
```bash
curl -s -X POST localhost:8000/api/colors/ -H 'Content-Type: application/json' -d '{"name": "Bad", "code": "red"}'
```
```json
{"error": {"code": "VALIDATION_ERROR", "message": "Invalid input.", "details": {"code": ["Color code must look like #RRGGBB."]}}}
```
A duplicate code gives `400 VALIDATION_ERROR` with `{"code": ["color with this code already exists."]}`.

### /api/inspections/
A QA checklist item for one garment type.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | int | read-only | |
| `name` | string | yes | max 120 chars |
| `garment_type` | enum | yes | |
| `description` | string | no | |
| `created_at`, `updated_at` | datetime | read-only | |

Query params: `garment_type`.
```bash
curl -s "localhost:8000/api/inspections/?garment_type=HEAT_INSULATION"
```
```json
{"count": 2, "next": null, "previous": null, "results": [
  {"id": 3, "name": "Heat resistance test", "garment_type": "HEAT_INSULATION", "description": "", "created_at": "...", "updated_at": "..."},
  {"id": 4, "name": "Seam strength", "garment_type": "HEAT_INSULATION", "description": "", "created_at": "...", "updated_at": "..."}]}
```
