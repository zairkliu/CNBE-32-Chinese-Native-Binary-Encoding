# Structure/Decomposition Review Packet

## Result

- Overall status: `PASS_STRUCTURE_DECOMPOSITION_REVIEW_PACKET_READY`
- Next workflow status: `HUMAN_OR_AGENT_REVIEW_ALLOWED_NO_SCORING`
- Source report: `reports/gf0017_structure_decomposition_evidence_repair_from_index.json`
- Source SHA-256: `a3336ef410d8441e15a55d0bb7e5f5b42973d997337e3f7b6d0f74148cd315f5`
- Source total rows: 97686
- Packet rows: 212
- Editable copy: `review_packets/structure_decomposition/structure_decomposition_review_packet_EDITABLE.csv`
- Full table duplicate allowed: `False`
- Database generation allowed: `False`
- XLSX generation allowed: `False`

The packet is a bounded review surface. It does not duplicate the full
97,686-row table, create a database, assign GF0017 points, or emit final
structure labels.

## Packet Status Counts

| Status | Count |
|---|---:|
| `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | 40 |
| `STRUCTURE_DECOMPOSITION_AGENT_STANDARD_QUEUE_ONLY` | 40 |
| `STRUCTURE_DECOMPOSITION_PARTIAL_REVIEW_REQUIRED` | 40 |
| `STRUCTURE_DECOMPOSITION_REVIEWABLE_CONTEXT_READY` | 40 |
| `STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_DICTIONARY_CONTEXT` | 12 |
| `STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_REVIEW_CONTEXT` | 40 |

## Editing Rule

Only the EDITABLE copy may be modified during review. The source repair report remains read-only evidence.

## Decision

A bounded review packet is ready. It references the existing 97,686-row source report and provides an explicitly marked editable copy for review notes only.
