# Remaining Structure Source Acquisition Plan

## Purpose

This report audits whether stronger local glyph, etymology, IDS, Unihan,
or dictionary resources can close the remaining structure/decomposition
source gaps after Wiki cross-reference.

It does not assign GF0017 scores, modify source assets, write CNBE rows,
rebuild databases, create tags, publish releases, or upload to PyPI.

## Result

- Overall status: `PASS_REMAINING_STRUCTURE_SOURCE_ACQUISITION_PLAN_READY`
- Next workflow status: `AGENT_STANDARD_REMAINING_STRUCTURE_PLAN_ALLOWED_FORMAL_SCORING_BLOCKED`
- Remaining rows: `73831`
- Stronger authoritative source available: `False`
- Score values assigned: `0`

## Candidate Resources

- `gf_gb_component_standards`: grade `direct_standard_for_rules_not_row_level_ids`, hits `0`, authoritative close `False`
- `unihan2`: grade `unicode_cross_reference_not_structure_authority`, hits `73831`, authoritative close `False`
- `unihan_zip_invalid`: grade `identity_failed`, hits `0`, authoritative close `False`
- `kangxi_4w`: grade `dictionary_cross_reference`, hits `28917`, authoritative close `False`
- `cjk_decomp`: grade `third_party_ids_cross_reference`, hits `89`, authoritative close `False`
- `decomp_data`: grade `third_party_dictionary_cross_reference`, hits `0`, authoritative close `False`

## Decision

No stronger local authoritative row-level IDS/resource was found for the remaining rows. Proceed with an Agent-standard plan that preserves all gaps as project-level candidates, not national-standard evidence.
