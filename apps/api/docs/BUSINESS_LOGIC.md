# Business Logic

This page lists every business rule as a numbered case, written so that a non-developer can read it. Each case names the code that enforces it and the automated test that proves it. See [API.md](API.md) for request/response formats.

Test files: `apps/orders/tests/test_services.py` (rules), `test_rules.py` (fabric table), `test_api.py` (HTTP behaviour), and `apps/catalog/tests/test_api.py` (catalog).

## 1. State machine

An order moves through 6 stages and ends as `DELIVERED`. Approving a stage moves it forward; rejecting sends it back according to the table.

| Status | Step | Next on approve | Target on reject | SLA (stage time limit) |
|---|---|---|---|---|
| `DESIGN` | 1 Design and pattern cutting | `FABRIC_PREP` | `DESIGN` | 27h (designer 24h + machine 3h) |
| `FABRIC_PREP` | 2 Fabric sourcing and prep | `FABRIC_DONE` | `FABRIC_PREP` | 36h (procurement 24h + measure 12h) |
| `FABRIC_DONE` | 3 Fabric finishing | `STITCHING` | `FABRIC_PREP` (workpiece rejected, back to step 2) | 60h (combine 12h + dyeing 48h) |
| `STITCHING` | 4 Assembly and stitching | `QA` | `STITCHING` | 48h |
| `QA` | 5 QA and inspection | `PACKAGING` | `STITCHING` (fails QC, back to step 4) | 12h |
| `PACKAGING` | 6 Packaging and delivery | `DELIVERED` | cannot reject (use "hold in staging") | 24h |
| `DELIVERED` | finished | none | cannot reject | none |

Code: `choices.py` (`NEXT_STATUS`, `REJECT_TARGET`, `STAGE_SLA_HOURS`). Test: `test_services.py::test_next_status_table`, `test_reject_routes`, `test_sla_hours_table`.

## 2. Fabric compatibility

The garment type chosen at step 1 limits which fabrics may be used.

| Garment type | Allowed fabrics |
|---|---|
| `GENERAL` | all 8 fabrics |
| `HEAT_INSULATION` | COTTON, DENIM, WOOL, ARAMID |
| `WATERPROOF` | POLYESTER, NYLON |
| `WINTER` | WOOL, FLEECE, DENIM, POLYESTER |
| `CHEAP` | COTTON, POLYESTER |

Worked example: a **kitchen apron** is `HEAT_INSULATION`. Cotton is allowed. **Polyester is not**, because polyester melts near heat, so the system refuses it with `FABRIC_INCOMPATIBLE`. It is available through `GET /api/fabric-rules/`.

Code: `rules.py::is_fabric_allowed`. Tests: `test_rules.py::test_heat_insulation_rejects_polyester`, `test_table_rows`.

Terms used below: **gate** is the check an order must pass to be approved. **Rework** is a rejection that sends the order back. **SLA** is the time limit of a stage.

---

## 3. Creating, editing and deleting orders

**Case 3.1 — Create an order with a valid fabric (R1)**
- Given a client orders a `HEAT_INSULATION` garment in `COTTON`.
- When they create the order.
- Then it is saved with status `DESIGN`, `rework_count` 0, and a `CREATED` event is logged (HTTP 201).
- Code: `services.py::create_order`
- Test: `test_services.py::test_create_logs_event_and_starts_in_design`, `test_api.py::test_create_order_and_response_fields`

**Case 3.2 — Create an order with an incompatible fabric (R1)**
- Given a client orders a `HEAT_INSULATION` garment in `POLYESTER`.
- When they create the order.
- Then nothing is saved. Error `FABRIC_INCOMPATIBLE` (HTTP 400); the details list the allowed fabrics.
- Code: `services.py::create_order` (via `_check_fabric`)
- Test: `test_services.py::test_r1_fabric_incompatible_on_create`, `test_api.py::test_create_incompatible_fabric_400`

**Case 3.3 — Edit an order while in DESIGN (R2)**
- Given an order in `DESIGN`.
- When the client changes `name`, `address`, `quantity`, `pattern`, `color`, `color_metric`, `fabric_type` or `garment_type`.
- Then the changes are saved and an `UPDATED` event is logged. Status can never be changed this way.
- Code: `services.py::update_order`
- Test: `test_services.py::test_r2_update_in_design_logs_updated`, `test_api.py::test_patch_cannot_change_status`

**Case 3.4 — Edit that breaks fabric compatibility (R2 + R1)**
- Given an order in `DESIGN` with `HEAT_INSULATION` and `COTTON`.
- When the client changes the fabric to `POLYESTER` (or the garment type to something that does not allow the current fabric).
- Then the edit is refused: `FABRIC_INCOMPATIBLE` (HTTP 400).
- Code: `services.py::update_order`
- Test: `test_services.py::test_r2_update_rechecks_r1`

**Case 3.5 — Edit an order after DESIGN (R2)**
- Given an order that is already past `DESIGN`.
- When the client tries to edit it.
- Then `ORDER_LOCKED` (HTTP 409).
- Code: `services.py::update_order` (via `_ensure_design_stage`)
- Test: `test_services.py::test_r2_update_locked_after_design`, `test_api.py::test_patch_and_locked_409`

**Case 3.6 — Delete an order in DESIGN (R3)**
- Given an order in `DESIGN`.
- When the client deletes it.
- Then it is removed (HTTP 204).
- Code: `services.py::delete_order`
- Test: `test_services.py::test_r3_delete_in_design`, `test_api.py::test_delete_and_locked`

**Case 3.7 — Delete an order after DESIGN (R3)**
- Given an order past `DESIGN`.
- When the client deletes it.
- Then `ORDER_LOCKED` (HTTP 409) and the order stays.
- Code: `services.py::delete_order`
- Test: `test_services.py::test_r3_delete_locked_after_design`

---

## 4. Stage gates (approve)

Every approval needs an `actor`. If the gate passes, the order moves to the next status, the SLA clock restarts and an `APPROVED` event is logged. If a gate fails, nothing changes.

### Stage DESIGN

**Case 4.1 — Approve DESIGN with a pattern**
- Given an order in `DESIGN` that has a pattern, or the request supplies a valid `pattern_id`.
- When the designer approves.
- Then the order moves to `FABRIC_PREP` (the supplied pattern is attached).
- Code: `services.py::_gate_design`
- Test: `test_services.py::test_design_accepts_pattern_id_in_payload`, `test_design_uses_pattern_already_on_order`

**Case 4.2 — Approve DESIGN without a pattern**
- Given an order in `DESIGN` with no pattern and no `pattern_id`.
- When the designer approves.
- Then `PATTERN_REQUIRED` (HTTP 400).
- Code: `services.py::_gate_design`
- Test: `test_services.py::test_design_requires_pattern`, `test_api.py::test_approve_pattern_required_then_ok`

### Stage FABRIC_PREP

**Case 4.3 — Approve FABRIC_PREP with a matching swatch**
- Given an order in `FABRIC_PREP` for `COTTON`.
- When the buyer sends `swatch_fabric_type` = `COTTON` and `measured_fabric_meters` = `25.50`.
- Then the meters are stored and the order moves to `FABRIC_DONE`.
- Code: `services.py::_gate_fabric_prep`
- Test: `test_services.py::test_fabric_prep_stores_meters`

**Case 4.4 — Swatch differs from the ordered fabric**
- Given an order for `COTTON`.
- When the swatch is `LINEN`, or no swatch is sent.
- Then `SWATCH_MISMATCH` (HTTP 400).
- Code: `services.py::_gate_fabric_prep`
- Test: `test_services.py::test_fabric_prep_swatch_mismatch`, `test_fabric_prep_missing_swatch_is_mismatch`

**Case 4.5 — Swatch fabric not allowed for the garment**
- Given the order's fabric is no longer allowed for its garment type.
- When the buyer approves with a swatch equal to the order's fabric.
- Then `FABRIC_INCOMPATIBLE` (HTTP 400). This is a safety net in case the table was changed after the order was created.
- Code: `services.py::_gate_fabric_prep` (via `_check_fabric`)
- Test: `test_services.py::test_fabric_prep_swatch_must_be_allowed`

**Case 4.6 — Measured meters missing or not positive**
- Given an order in `FABRIC_PREP` with a matching swatch.
- When `measured_fabric_meters` is missing, zero or negative.
- Then `VALIDATION_ERROR` (HTTP 400).
- Code: `services.py::_gate_fabric_prep` (via `_require_positive`)
- Test: `test_services.py::test_fabric_prep_meters_must_be_positive`

### Stage FABRIC_DONE

**Case 4.7 — Approve FABRIC_DONE**
- Given an order in `FABRIC_DONE` with measured fabric of 25.50 m and a color (already on the order or given as `color_id`).
- When the dyer sends `finished_fabric_meters` of 24.00 (equal to 25.50 is also fine).
- Then the meters are stored and the order moves to `STITCHING`.
- Code: `services.py::_gate_fabric_done`
- Test: `test_services.py::test_fabric_done_ok_equal_to_measured`

**Case 4.8 — No color**
- Given an order in `FABRIC_DONE` with no color and no `color_id`.
- When the dyer approves.
- Then `COLOR_REQUIRED` (HTTP 400). An unknown `color_id` gives `VALIDATION_ERROR`.
- Code: `services.py::_gate_fabric_done`
- Test: `test_services.py::test_fabric_done_requires_color`

**Case 4.9 — Finished fabric more than measured fabric**
- Given measured fabric of 25.50 m.
- When the dyer reports 30 m finished.
- Then `YIELD_EXCEEDS_MEASURED` (HTTP 400), because you cannot finish more fabric than you measured.
- Code: `services.py::_gate_fabric_done`
- Test: `test_services.py::test_fabric_done_yield_exceeds_measured`

**Case 4.10 — Finished meters missing or not positive**
- Given an order in `FABRIC_DONE` with a color.
- When `finished_fabric_meters` is missing, zero or negative.
- Then `VALIDATION_ERROR` (HTTP 400).
- Code: `services.py::_gate_fabric_done` (via `_require_positive`)
- Test: `test_services.py::test_fabric_done_finished_must_be_positive`

### Stage STITCHING

**Case 4.11 — Piece count matches the order**
- Given an order of quantity 10 in `STITCHING`.
- When the sewer reports `assembled_pieces_count` = 10.
- Then the count is stored and the order moves to `QA`.
- Code: `services.py::_gate_stitching`
- Test: `test_services.py::test_stitching_ok`

**Case 4.12 — Piece count does not match**
- Given an order of quantity 10.
- When the sewer reports 9 (or sends nothing).
- Then `PIECE_COUNT_MISMATCH` (HTTP 400).
- Code: `services.py::_gate_stitching`
- Test: `test_services.py::test_stitching_piece_count_mismatch`

### Stage QA

The QA checklist is the set of inspections defined for the order's garment type (see `/api/inspections/`).

**Case 4.13 — All inspections answered and passed**
- Given a `HEAT_INSULATION` order in `QA` and two inspections (ids 3 and 4) for that garment type.
- When QA sends both results with `passed: true`.
- Then the order moves to `PACKAGING` and the results are saved in the event data.
- Code: `services.py::_gate_qa`
- Test: `test_services.py::test_qa_results_saved_in_event`, `test_full_happy_path_events`

**Case 4.14 — Some inspections not answered**
- Given inspections 3 and 4 exist for the garment type.
- When QA only answers inspection 3.
- Then `INSPECTION_INCOMPLETE` (HTTP 400) with `missing_inspection_ids: [4]`.
- Code: `services.py::_gate_qa`
- Test: `test_services.py::test_qa_incomplete_results`

**Case 4.15 — An inspection failed**
- Given all inspections are answered.
- When at least one has `passed: false`.
- Then `QC_FAILED` (HTTP 400). The caller should reject the order instead (see case 5.5).
- Code: `services.py::_gate_qa`
- Test: `test_services.py::test_qa_failed_item`

**Case 4.16 — Unknown inspection id**
- Given the results contain an id that is not an inspection of this garment type.
- When QA approves.
- Then `VALIDATION_ERROR` (HTTP 400).
- Code: `services.py::_gate_qa`
- Test: `test_services.py::test_qa_unknown_inspection_is_validation_error`

**Case 4.17 — Garment type with no inspections**
- Given no inspection exists for the order's garment type.
- When QA approves without results.
- Then the order moves to `PACKAGING`.
- Code: `services.py::_gate_qa`
- Test: `test_services.py::test_qa_without_inspections_allowed`

### Stage PACKAGING

**Case 4.18 — Approve PACKAGING when ready**
- Given an order in `PACKAGING` marked ready for dispatch (see case 6.1).
- When the packer approves with a `tracking_number`.
- Then the tracking number is stored and the order becomes `DELIVERED`.
- Code: `services.py::_gate_packaging`
- Test: `test_api.py::test_full_flow_via_api`, `test_services.py::test_full_happy_path_events`

**Case 4.19 — Approve PACKAGING when not ready**
- Given an order in `PACKAGING` that is not marked ready (or is on hold).
- When the packer approves.
- Then `NOT_READY_FOR_DISPATCH` (HTTP 400).
- Code: `services.py::_gate_packaging`
- Test: `test_services.py::test_packaging_not_ready`, `test_api.py::test_not_ready_for_dispatch_400`

**Case 4.20 — Tracking number missing**
- Given a ready order in `PACKAGING`.
- When the packer approves with a blank or missing `tracking_number`.
- Then `VALIDATION_ERROR` (HTTP 400).
- Code: `services.py::_gate_packaging`
- Test: `test_services.py::test_packaging_requires_tracking_number`

### Stage DELIVERED

**Case 4.21 — Approve a delivered order**
- Given an order that is `DELIVERED`.
- When someone approves it.
- Then `ORDER_COMPLETED` (HTTP 409).
- Code: `services.py::_gate_delivered`
- Test: `test_services.py::test_delivered_cannot_be_approved`

**Case 4.22 — Approve without an actor**
- Given any order.
- When the request has no `actor`.
- Then `VALIDATION_ERROR` (HTTP 400).
- Code: `serializers.py::ApproveInputSerializer` (shape check only)
- Test: `test_api.py::test_approve_requires_actor`

---

## 5. Rejecting an order

A reject needs an `actor` and a non-blank `reason`. The order goes to the target in the state machine table, `rework_count` goes up by 1, the SLA clock restarts, and a `REJECTED` event is logged with `data: {"from": ..., "to": ...}`.

**Case 5.1 — Reject in DESIGN, FABRIC_PREP or STITCHING (redo the same stage)**
- Given an order in one of these stages.
- When it is rejected with a reason.
- Then it stays in the same status (the work is redone) and `rework_count` becomes 1.
- Code: `services.py::reject`
- Test: `test_services.py::test_reject_routes[DESIGN]`, `[FABRIC_PREP]`, `[STITCHING]`

**Case 5.2 — Reject in FABRIC_DONE (workpiece rejected)**
- Given an order in `FABRIC_DONE`.
- When it is rejected.
- Then it goes back to `FABRIC_PREP` (step 2).
- Code: `services.py::reject`
- Test: `test_services.py::test_reject_routes[FABRIC_DONE]`

**Case 5.3 — Reject in QA (fails quality control)**
- Given an order in `QA`.
- When it is rejected.
- Then it goes back to `STITCHING` (step 4). Example: `POST /reject/` with reason "Loose stitching on seams".
- Code: `services.py::reject`
- Test: `test_services.py::test_reject_routes[QA]`, `test_api.py::test_reject_endpoint`

**Case 5.4 — Rework counter accumulates**
- Given an order that was rejected once.
- When it is rejected again later.
- Then `rework_count` is 2, and so on. It is never reset.
- Code: `services.py::reject`
- Test: `test_services.py::test_rework_count_accumulates`

**Case 5.5 — QC failed, so reject instead of approve**
- Given a QA result with a failed inspection (case 4.15).
- When the inspector uses `/reject/` with a reason.
- Then the order returns to `STITCHING` (case 5.3).
- Code: `services.py::reject`
- Test: `test_services.py::test_reject_routes[QA]`

**Case 5.6 — Reject in PACKAGING or DELIVERED**
- Given an order in `PACKAGING` or `DELIVERED`.
- When someone rejects it.
- Then `REJECT_NOT_ALLOWED` (HTTP 409). To pause packaging, use "hold in staging" (case 6.2).
- Code: `services.py::reject`
- Test: `test_services.py::test_reject_not_allowed_in_packaging`, `test_reject_not_allowed_when_delivered`, `test_api.py::test_reject_not_allowed_409`

**Case 5.7 — Reject without a reason**
- Given an order in a rejectable stage.
- When `reason` is missing or blank.
- Then `VALIDATION_ERROR` (HTTP 400).
- Code: `services.py::reject` (blank check); `serializers.py::RejectInputSerializer` (missing field)
- Test: `test_services.py::test_reject_requires_reason`

---

## 6. Ready-for-dispatch (PACKAGING)

**Case 6.1 — Mark ready**
- Given an order in `PACKAGING`.
- When the packer sends `is_ready: true` and `cartons_count` of 1 or more.
- Then `is_ready_dispatch` becomes true, cartons are stored, and `READY_DISPATCH_SET` is logged. The order stays in `PACKAGING` until approved.
- Code: `services.py::set_ready_dispatch`
- Test: `test_services.py::test_ready_dispatch_hold_and_ready`

**Case 6.2 — Hold in finished goods staging area**
- Given an order in `PACKAGING`.
- When the packer sends `is_ready: false`.
- Then the order is held (`is_ready_dispatch` false). It cannot be approved until it is marked ready (case 4.19). No cartons are needed.
- Code: `services.py::set_ready_dispatch`
- Test: `test_services.py::test_ready_dispatch_hold_and_ready`

**Case 6.3 — Ready without cartons**
- Given an order in `PACKAGING`.
- When `is_ready: true` is sent with no `cartons_count` or one below 1.
- Then `VALIDATION_ERROR` (HTTP 400).
- Code: `services.py::set_ready_dispatch`
- Test: `test_services.py::test_ready_dispatch_needs_cartons`, `test_api.py::test_ready_dispatch_needs_cartons_400`

**Case 6.4 — Wrong stage**
- Given an order that is not in `PACKAGING`.
- When ready-dispatch is called.
- Then `INVALID_STAGE` (HTTP 409).
- Code: `services.py::set_ready_dispatch`
- Test: `test_services.py::test_ready_dispatch_invalid_stage`, `test_api.py::test_ready_dispatch_invalid_stage_409`

---

## 7. SLA and overdue

**Case 7.1 — Stage time limit**
- Given an order enters a stage (for example `QA`, limit 12h).
- When you read the order.
- Then `sla_hours` is 12, `sla_deadline` is `stage_started_at` + 12h, and `next_status` shows where an approval would send it.
- Code: `models.py::Order.sla_hours`, `sla_deadline`; `choices.py::STAGE_SLA_HOURS`
- Test: `test_services.py::test_sla_hours_table`

**Case 7.2 — Becoming overdue**
- Given an order whose deadline has passed.
- When you read it.
- Then `is_overdue` is true. `GET /api/orders/?overdue=true` lists these orders.
- Code: `models.py::Order.is_overdue`, `services.py::filter_overdue`
- Test: `test_services.py::test_is_overdue_after_deadline`, `test_filter_overdue_queryset`, `test_api.py::test_overdue_filter`

**Case 7.3 — Delivered orders are never overdue**
- Given a `DELIVERED` order.
- When you read it.
- Then `sla_hours` and `sla_deadline` are null and `is_overdue` is false.
- Code: `models.py::Order.is_overdue`
- Test: `test_services.py::test_delivered_never_overdue`

**Case 7.4 — The clock restarts on every move**
- Given an order in any stage.
- When it is approved or rejected (even a reject that leaves the status unchanged).
- Then `stage_started_at` is reset to now, so the new stage gets its full time limit.
- Code: `services.py::_move_to`
- Test: `test_services.py::test_stage_clock_resets_on_approve_and_reject`

---

## 8. Catalog rules

**Case 8.1 — Cannot delete a pattern or color that is in use**
- Given a pattern (or color) that an order references.
- When a client deletes it.
- Then `IN_USE` (HTTP 409) and it stays. Unused ones can be deleted.
- Code: `apps/common/exception_handler.py::api_exception_handler` (turns the database `ProtectedError` into `IN_USE`); orders reference them with `on_delete=PROTECT`.
- Test: `apps/catalog/tests/test_api.py::test_delete_pattern_in_use_is_protected`

**Case 8.2 — Color code must be `#RRGGBB`**
- Given a client creates a color.
- When the code is not `#` plus 6 hex digits (for example `red`).
- Then `VALIDATION_ERROR` (HTTP 400).
- Code: `apps/catalog/models.py::HEX_COLOR_VALIDATOR`
- Test: `apps/catalog/tests/test_api.py::test_color_code_invalid`

**Case 8.3 — Color codes are stored in uppercase and unique**
- Given a color `#abcdef` exists.
- When a client saves `#ABCDEF` as another color.
- Then the code is stored as `#ABCDEF`, and a duplicate (in any letter case) gives `VALIDATION_ERROR`. Re-saving a color with its own code is fine.
- Code: `apps/catalog/serializers.py::ColorSerializer.validate_code`
- Test: `apps/catalog/tests/test_api.py::test_color_crud_uppercases_code`, `test_color_code_unique_case_insensitive`, `test_color_update_same_code_ok`

**Case 8.4 — Pattern piece count at least 1**
- Given a client creates a pattern.
- When `piece_count` is 0.
- Then `VALIDATION_ERROR` (HTTP 400).
- Code: `apps/catalog/models.py::Pattern.piece_count`
- Test: `apps/catalog/tests/test_api.py::test_pattern_piece_count_min_1`
