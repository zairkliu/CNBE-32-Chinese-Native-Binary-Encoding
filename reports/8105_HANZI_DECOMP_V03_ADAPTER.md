# Hanzi Decomp v0.3 8105 Adapter

- Overall status: `PASS_HANZI_DECOMP_V03_ADAPTER_READY_FOR_REVIEW`
- Source packet rows: 8105
- IDS data rows: 88343
- 8105 coverage: 8075
- Gap-fill candidate rows: 1243
- Conflict rows: 357
- CNBE32 rows written: 0
- Database rebuild allowed: `False`

The tool is treated as `USER_SUPPLIED_PROGRAM_AGENT_REFERENCE_NOT_NATIONAL_STANDARD`.
Its structure codes are review candidates only.

## Tool Risks

| Risk | Present |
|---|---:|
| `hardcoded_windows_base_path` | `True` |
| `opens_browser` | `True` |
| `starts_local_http_server` | `True` |
| `uses_subprocess` | `True` |
| `writes_files` | `True` |

## Status Counts

| Status | Rows |
|---|---:|
| `TOOL_CONFIRMS_CURRENT` | 6475 |
| `TOOL_CONFLICT_REVIEW_REQUIRED` | 357 |
| `TOOL_FILLS_CURRENT_GAP_REVIEW_REQUIRED` | 1243 |
| `TOOL_GAP` | 30 |

## Decision

Review the gap-fill candidates first, and separately audit the conflicts before any source merge or encoding write.
