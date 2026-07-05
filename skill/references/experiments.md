# CNBE-32 Experiment Design Reference (v1-v7)

## v1: Single-Character Validation

- **Test**: Can LLM understand CNBE-32 encoding zero-shot?
- **Data**: 200 single characters with CNBE annotations
- **Prompt**: "这是什么字？"[CNBE annotation]
- **Expected**: 100% effective rate on qwen3.5:0.8b
- **White paper**: `llm_experiments/v1_v4_validation/CNBE-32_Ollama_*_v1.md`

## v2: Sentence Understanding

- **Test**: Does CNBE improve sentence understanding?
- **Data**: 100 sentences (50 classical + 50 modern, 20-50 chars each)
- **Control**: Pure text, "用一句话概括核心含义"
- **CNBE**: Text with format A per-char annotation
- **Expected**: 48% -> 87% (+81%) on qwen3.5:0.8b
- **White paper**: `llm_experiments/v1_v4_validation/CNBE-32_v2_*.md`

## v3: Format Optimization

- **Test**: Which CNBE injection format works best?
- **Formats**: A (per-char annotation), B (text translation), C (student format)
- **Winner**: Format A — 87% effective, only 9% distraction rate
- **White paper**: `llm_experiments/v1_v4_validation/CNBE-32_v3_*.md`

## v4: Long Text (On Protracted War)

- **Test**: Does CNBE help with full-paper comprehension?
- **Data**: 22 key paragraphs from Mao's "On Protracted War"
- **Control**: 90.9% -> CNBE: 100% (+9.1%)
- **White paper**: `llm_experiments/v1_v4_validation/CNBE-32_v4_*.md`

## v5: Multi-Model Comparison

- **Test**: How does CNBE benefit vary across model sizes?
- **Models**: 0.8B, 2B, 4B, 8B, 9B, 20B (7 total, both CN and foreign)
- **Key finding**: Benefit decreases with model size
- **White papers**: `llm_experiments/v5_model_comparison/`

## v6: Numerical Format & Hard Tasks

- **Test**: Can models understand CNBE as raw numbers?
- **Formats**: C (bracket), D (space), F (packed) — compared with Unicode numerical
- **Findings**: Format F (bare packed numbers) is optimal. CNBE > Unicode on Gemma 4B (+17.4pp)
- **Hard task**: Traditional Chinese, rare chars, chemistry formulas
- **White papers**: `llm_experiments/v6_numerical_features/`

## v7: RISC-V Hardware

- **Test**: CNBE skill table implementation on RISC-V
- **Metrics**: x86: 0.8ns, QEMU RISC-V: 2.5ns, FPGA: 1 cycle
- **Custom instructions**: cnhe.map, cnhe.extract, cnhe.cmp (Spike integrated)
- **White papers**: `riscv/` (v7.0 through v7.2)
