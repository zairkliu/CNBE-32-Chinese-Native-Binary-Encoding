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


## v7.3: Feature Space Co-validation

- **Test**: Can CNBE Format F (3D features: radical/stroke/structure) be directly parsed by ML classifiers?
- **Data**: 418 character pairs across 6 categories, 241 unique chars
- **Methods**: Cosine similarity + silhouette score + KNN classification
- **Findings**: CNBE is only format with positive radical separation (+0.0294). CNBE wins 2/3 hard tasks (stroke +4.6pp, structure +10.4pp)
- **Significance**: Validates that CNBE's 3-byte format F carries usable structural features without any embedding model
- **White paper**: `experiments/v73/CNBE-32_v7.3_硬件编码+特征空间协同验证白皮书.md`

## v8.0: Chinese Programming Language Compiler

- **Test**: Can a Chinese programming language be compiled to CNBE-enhanced RISC-V assembly?
- **Data**: 3 test programs (loop sum, structure compare, semantic cluster)
- **Implementation**: Complete lexer/parser/codegen toolchain (lexer.py: 23 keywords, parser.py: recursive descent, codegen.py: 34+ insns)
- **Findings**: test_loop.cnbe compiles to 34 valid RISC-V instructions with loop/condition/output/exit. Chinese keywords map to CNBE functions
- **Significance**: Proves "Chinese source -> CNBE RISC-V" full-stack feasibility
- **White paper**: `v8_chinese_programming/CNBE-32_v8.0_中文编程映射实验白皮书.md`

## v8.1: Complete Compiler + Skill Table Integration

- **Test**: Complete the compiler, fix all bugs, integrate 81.6KB skill table into runtime
- **Achievements**: All 4 test programs compile (test_loop:34, test_struct:48, test_cluster:27, test_array:34 insns). String literal support added. Digit-suffixed Chinese identifiers supported. 20902-entry skill table embedded in C runtime
- **Significance**: Production-ready compiler prototype with real CNBE lookup (not stubs). Complete path from Chinese source -> RISC-V assembly -> runtime link
- **White paper**: `v8_chinese_programming/CNBE-32_v8.1_完整编译器+Skill表集成+Spike验证白皮书.md`
