# CNBE-32: Comparison with Existing Approaches

## Algorithm Layer

- ChineseBERT (ACL 2021): Renders characters as images for glyph features -- software only
- Glyph2Vec / Radical Embedding: Used in font conversion, OCR -- data level only

## Data Layer

- Unicode IDS: Describes structure with text symbols -- CPU does not compute
- CHISE (Japan): Large character structure database -- for lookup only
- Cangjie/Wubi: Input methods -- human-to-machine mapping

## Hardware Layer

**CNBE-32 is the only known project** that integrates Chinese character structure into CPU instruction sets, OS kernels, and machine encoding at the binary level.

## Similar Efforts

- FuXi-128: Uses Chinese characters as CPU instruction mnemonics -- conceptual/educational only
