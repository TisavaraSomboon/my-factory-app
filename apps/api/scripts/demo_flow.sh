#!/usr/bin/env bash
# End-to-end demo: one kitchen apron order from creation to DELIVERED.
# Requires: server running + seed data (make up && make seed). Needs only curl + python3.
# Usage: ./scripts/demo_flow.sh [base_url]
set -euo pipefail
BASE="${1:-http://localhost:8000/api}"
J='Content-Type: application/json'

call() { # call METHOD PATH [JSON]
  echo -e "\n\033[1;34m>>> $1 $2\033[0m ${3:-}"
  curl -s -X "$1" "$BASE$2" -H "$J" ${3:+-d "$3"} -w '\n[HTTP %{http_code}]\n'
}
field() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }

# Look up seed ids by name (so the script works regardless of id numbers)
PATTERN=$(curl -s "$BASE/patterns/" | python3 -c "import sys,json; print(next(r['id'] for r in json.load(sys.stdin)['results'] if r['pattern_type']=='APRON'))")
COLOR=$(curl -s "$BASE/colors/" | python3 -c "import sys,json; print(json.load(sys.stdin)['results'][0]['id'])")
INSPECTIONS=$(curl -s "$BASE/inspections/?garment_type=HEAT_INSULATION" | python3 -c "
import sys,json; print(json.dumps([{'inspection_id': r['id'], 'passed': True} for r in json.load(sys.stdin)['results']]))")

echo "== Case 1: polyester apron is rejected (FABRIC_INCOMPATIBLE)"
call POST /orders/ '{"name":"Apron (poly)","garment_type":"HEAT_INSULATION","fabric_type":"POLYESTER","requester_username":"somchai","address":"Bangkok","quantity":10}'

echo "== Case 2: create a valid cotton apron"
ID=$(curl -s -X POST "$BASE/orders/" -H "$J" -d '{"name":"Kitchen apron x10","garment_type":"HEAT_INSULATION","fabric_type":"COTTON","requester_username":"somchai","address":"Bangkok","quantity":10}' | field "['id']")
echo "created order id=$ID"

echo "== Step 1 DESIGN"
call POST "/orders/$ID/approve/" '{"actor":"designer"}'                                   # PATTERN_REQUIRED
call POST "/orders/$ID/approve/" "{\"actor\":\"designer\",\"pattern_id\":$PATTERN}"

echo "== Step 2 FABRIC_PREP"
call POST "/orders/$ID/approve/" '{"actor":"buyer","swatch_fabric_type":"POLYESTER","measured_fabric_meters":"15"}'  # SWATCH_MISMATCH
call POST "/orders/$ID/approve/" '{"actor":"buyer","swatch_fabric_type":"COTTON","measured_fabric_meters":"15"}'

echo "== Step 3 FABRIC_DONE (reject once -> back to FABRIC_PREP, then redo)"
call POST "/orders/$ID/reject/" '{"actor":"dyer","reason":"Uneven dye lot"}'
call POST "/orders/$ID/approve/" '{"actor":"buyer","swatch_fabric_type":"COTTON","measured_fabric_meters":"15"}'
call POST "/orders/$ID/approve/" "{\"actor\":\"dyer\",\"color_id\":$COLOR,\"finished_fabric_meters\":\"20\"}"  # YIELD_EXCEEDS_MEASURED
call POST "/orders/$ID/approve/" "{\"actor\":\"dyer\",\"color_id\":$COLOR,\"finished_fabric_meters\":\"14.5\"}"

echo "== Step 4 STITCHING"
call POST "/orders/$ID/approve/" '{"actor":"line-lead","assembled_pieces_count":9}'      # PIECE_COUNT_MISMATCH
call POST "/orders/$ID/approve/" '{"actor":"line-lead","assembled_pieces_count":10}'

echo "== Step 5 QA"
call POST "/orders/$ID/approve/" "{\"actor\":\"qa\",\"results\":$INSPECTIONS}"

echo "== Step 6 PACKAGING"
call POST "/orders/$ID/approve/" '{"actor":"packer","tracking_number":"TH123"}'          # NOT_READY_FOR_DISPATCH
call POST "/orders/$ID/ready-dispatch/" '{"actor":"packer","is_ready":true,"cartons_count":2}'
call POST "/orders/$ID/approve/" '{"actor":"packer","tracking_number":"TH123456789"}'

echo "== Result"
call GET "/orders/$ID/"
call GET "/orders/$ID/events/"
call POST "/orders/$ID/approve/" '{"actor":"x"}'                                          # 409 ORDER_COMPLETED
