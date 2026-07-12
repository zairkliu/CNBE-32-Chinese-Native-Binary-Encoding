# CNBE-32 Mapping Provenance Audit

## Technical Summary

No current mapping has enough evidence to become the canonical CNBE-32 semantic mapping. The SDK mapping is fully
reproducible but generated from Unicode-position modulo heuristics. The 97,686-row catalog has a strong historical
artifact chain, and its Unicode 17.0.0 source plus complete radical-based structure rule were recovered locally.

**Canonical mapping gate: NO_GO.** Preserve both mappings under their current boundaries; do not replace the SDK or
publish the full catalog as an authoritative linguistic mapping.

## Two Different Evidence Strengths

| Mapping | Artifact identity | Algorithm reproducibility | Upstream traceability | Semantic authority |
|---|---|---|---|---|
| Packaged SDK | Strong | Strong | Heuristic, no upstream source | Insufficient |
| 97,686-row catalog | Strong | Strong with local input | Recovered, not pinned | Insufficient |

The distinction matters: reproducibility establishes that the same numbers can be regenerated. It does not establish that
those numbers correctly represent a character's radical, strokes, or structure.

## SDK Mapping Is Exactly Reproducible but Heuristic

- Rows inspected: **20,902**
- SQLite integrity: **ok**
- Rows differing from the tracked modulo formula: **0**
- Database SHA-256: `9bea5a8bcec1c85cf7f51f827964b2f18dd904d1db349447ae3b97892e3a6740`
- Introduction commit: `7244e3e14875cd3492c15eb567ac32d6ede1a79a`

The tracked generator assigns radical, stroke count, structure, and index from the character's sequential Unicode
offset using modulo operations. This is deterministic engineering test data, not evidence-backed linguistic
annotation. Its authority is therefore limited to preserving the existing SDK compatibility contract.

## Full Catalog Has a Strong Historical Artifact Chain

- Workbook rows: **97,686**
- Workbook SHA-256: `d9e24432b9ef3bb20458179258a0371ccf7e699d02ff8b00b59c615ba2aaee84`
- Byte-identical to historical workbook blob: **True**
- Same Unicode keys as historical compressed SQLite: **True**
- CNBE differences versus historical SQLite: **0**
- Historical artifact commit: `83d29eca822bd8089b780521458ee8505a1b4ba4`

This establishes that the supplied workbook is the same artifact lineage committed in July 2026. It does not reconstruct how
the artifact was produced from upstream character data.


## Unicode 17.0.0 Source Was Recovered Locally

- Unihan SHA-256: `f7a48b2b545acfaa77b2d607ae28747404ce02baefee16396c5d2d7a8ef34b5e`
- Unicode version: **17.0.0**
- Catalog radical coverage/mismatches: **97,686 / 0**
- Catalog stroke coverage/mismatches after the 31 clamp: **97,686 / 0**
- Group-index mismatches across 4,425 groups: **0**
- Structure code/name mismatches: **0 / 0**
- Recovered structure rule: **PASS**
- License reference embedded in the archive: `https://www.unicode.org/terms_of_use.html`

This substantially strengthens the full-catalog lineage: radical and stroke fields are reproducible from the recovered
source, while structure and index fields are reproducible from documented deterministic rules. The archive remains
external to the repository, so the input chain is not yet repository-controlled.


## Raw-to-Catalog Algorithm Is Reconstructed

Historical documentation says the catalog used Unihan V17 radical/stroke data and heuristic structure rules. The
recovered archive confirms all radical and stroke assignments, deterministic grouping confirms all index assignments,
and the documented 19-override radical classifier reproduces all structure codes and names with zero differences. The
tracked historical `generate_cnbe_table.py` consumes an existing workbook, but the newly recovered classifier closes
the algorithmic structure-field gap.

Consequently, the workbook is algorithmically reproducible with the recovered local Unihan input. It is still not
semantically authoritative: the structure field is a radical-level heuristic and does not perform character-level
glyph decomposition.

## Methods and Definitions

The audit used four independent checks:

1. Recomputed every SDK row from the formula present in `tools/generate_mapping.py`.
2. Compared the supplied workbook bytes with historical Git blob `352e91956af4d64df7cf9ff37a88a6beb0f66822`.
3. Compared all workbook Unicode/CNBE pairs with the historical compressed SQLite blob `27e3e9282e8f29f4c7a04e40188fddda79809391`.
4. Reconstructed all structure fields from the documented 19 radical overrides and fallback rule.

"Artifact identity" means exact bytes or exact row values match historical repository objects. "Algorithm
reproducibility" means tracked code and pinned inputs can regenerate the mapping. "Semantic authority" means the
field values have traceable, reviewed evidence for their linguistic meaning.

## Limitations and Uncertainty

- Git history records what was committed, not the external legal status of upstream datasets.
- Historical prose claims are supporting context, not substitutes for pinned inputs and executable generation code.
- This audit does not independently judge every Unihan radical/stroke value or heuristic structure label.
- The exact reason the SDK chose the U+9FA5 cutoff is strongly suggested by code history but not documented as a
  formal compatibility decision.

## Required Next Steps

1. Add a checksum-pinned retrieval procedure for Unicode 17.0.0 Unihan and preserve its license notice.
2. Pin the recovered structure-classification rules and their historical evidence references.
3. Mark every field as source-derived, manually overridden, or heuristic.
4. Define a versioned canonical mapping and migration policy before changing existing SDK codes.
5. Run an independently reviewed stratified sample before making semantic-accuracy claims.

## Further Questions

- Is the original Unihan archive used in July 2026 still available on a development machine or backup?
- Was there an uncommitted script between Unihan extraction and the final workbook?
- Which mapping is intended to retain backward compatibility, and which may be versioned as a new mapping family?
- What redistribution notice is required for the upstream character-property data?
