# CNBE-32



**Chinese Native Binary Encoding**



A 32-bit encoding that embeds the structural semantics of Chinese characters (radical, stroke count, and structure type) directly into binary, exploring how CPUs and AI can natively understand Chinese.



A structured 32-bit encoding for 97,686 CJK characters that embeds radical, stroke count, and structure type directly into the encoding space.



<p align="center">

  <a href="docs/specification/bit-layout.md"><img src="https://img.shields.io/badge/Encoding-32--bit%20CNBE-blue?style=for-the-badge" alt="Encoding"></a>

  <a href="docs/specification/riscv-instructions.md"><img src="https://img.shields.io/badge/ISA-RISC--V%20Custom-green?style=for-the-badge" alt="ISA"></a>

  <a href="v84_riscv_os_full/"><img src="https://img.shields.io/badge/OS-Full%20Chinese%20Shell-orange?style=for-the-badge" alt="OS"></a>

  <a href="docs/VISION.md"><img src="https://img.shields.io/badge/Vision-2035%20Digital%20China-red?style=for-the-badge" alt="Vision"></a>

  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Mulan%20PSL%20v2-lightgrey?style=for-the-badge" alt="License"></a>

</p>



<p align="center">

  <a href="#quick-start"><strong>[ Quick Start ]</strong></a>

  <a href="#key-experiments"><strong>[ Key Experiments ]</strong></a>

  <a href="#tech-stack"><strong>[ Tech Stack ]</strong></a>

  <a href="#how-to-contribute"><strong>[ How to Contribute ]</strong></a>

</p>



---



## Architecture Panorama



```mermaid

graph TD

    A[Chinese Character Input] -->|Radical/Stroke Count/Structure| B(CNBE-32 Encoder)

    B -->|32-bit Binary| C{RISC-V Custom Instruction Set}

    C -->|cnhe.map / cnhe.cmp| D[Hardware Layer: Spike/QEMU/FPGA]

    D --> E[System Layer: Full Chinese Shell]

    E --> F[Chinese BASIC / JEPA Semantic Engine]

```



---


## Background & Research Motivation

This project is motivated by a simple observation: mainstream computing infrastructure has been built on the Latin alphabet and English-centric conventions, while over 1.3 billion Chinese speakers interact with technology through a fundamentally different writing system. CNBE-32 is an **experimental research exploration** of whether embedding Chinese character structure (radical, stroke count, spatial composition) directly into binary encoding can provide a more effective representational basis for machine understanding of Chinese.

The core research question is:

> **Does encoding the visual-structural features of Chinese characters as a 32-bit bitfield provide small-scale language models (<1B params) with a better inductive bias than flat Unicode codepoints?**

This is **not** a "Digital China" project, **not** an alternative to Unicode, **not** a "domestic OS" initiative, and **not** a practical product. It is a narrowly-scoped academic exploration at the intersection of Chinese linguistics, NLP representation learning, and computer architecture.

## 🎯 Project Positioning: A Technical Validation of CNHE Theory

### 1. Relationship to the Paper "Language Sovereignty and Digital Governance"

This project serves as the **systematic technical validation** of the **Chinese Native Hierarchical Encoding (CNHE)** concept proposed in the paper *Language Sovereignty and Digital Governance: Pathways to a Chinese Native AI Governance System* — a strategic analysis of why Chinese requires an independent encoding representation in the AI era.

The paper argues for CNHE at the strategic and governance level. This project answers the following question at the code level:

> **"Is CNHE constructible, runnable, and verifiable in real software and hardware environments?"**

The codebase implements the core encoding layer of CNHE (32-bit structured bitfield) and extends it to NLP experiments, RISC-V instruction set extensions, and operating system adaptations — testing the practical feasibility of embedding Chinese structural semantics directly into binary space.

| Layer | CNHE Paper (Strategic) | CNBE-32 Project (Validation) |
| :--- | :--- | :--- |
| **Encoding** | Proposes CNHE encoding | Implements 32-bit bitfield (radix/stroke/structure) |
| **Semantics** | Argues for structural mapping | Provides SQLite DB (20,902 chars) + NLP experiments |
| **Hardware** | Envisions native CPU support | RISC-V custom instruction RTL simulation (board-level pending) |
| **Timeline** | Positions for 2035 vision | Proves rapid prototyping is feasible in 2026 |

**CNBE-32 = A Runnable Technical Proof of CNHE Theory.**

### 2. Why This Project Could Only Emerge in 2026

This project is the product of three technological variables converging in 2026:

| Variable | Status in 2026 | Significance |
| :--- | :--- | :--- |
| **AI Code Generation** | Handles 90% of engineering heavy lifting | Compresses "encoding design to full-stack validation" from years to months |
| **RISC-V Open Ecosystem** | Spike/QEMU simulation tools mature | Enables instruction extension validation without tape-out |
| **Open-source AI Models** | Qwen, Gemma run locally | Allows controlled experiments comparing encoding schemes |

Before 2020, an independent researcher could not simultaneously work across NLP, databases, instruction sets, OS kernels, and FPGA simulation. The maturation of AI coding in 2026 has made this full-stack validation possible for a single researcher.

### 3. Triple Positioning

| Level | Positioning | Description |
| :--- | :--- | :--- |
| **Strategic** | A technical footnote to the CNHE paper | Runnable code demonstrates CNHE is realizable in binary space |
| **Research** | An experimental platform for Chinese structural encoding | Encoding tables, PyTorch baselines, comparative data |
| **Methodological** | A specimen of AI-assisted full-stack research | Documents boundaries of "human + AI" complex system construction |

### 4. Current Project Status

This project is an **extremely early-stage Proof of Concept (PoC)** exploring the technical feasibility of a long-term vision — not a production-ready system.

**Completed Validations:**
- ✅ Core CNHE bitfield design → 20,902 character database
- ✅ Small-scale NLP experiments → Positive effects on <1B models
- ✅ RISC-V instruction RTL simulation → Single-cycle lookup (board-level pending)

**Pending Validations:**
- ⏳ OS kernel adaptation → Known architectural issues, code does not compile
- ⏳ Large-scale validation → Requires third-party independent reproduction
- ⏳ Large model (>7B) mechanism → Gains approach zero, requires theoretical breakthrough

**The core value at this stage is to provide a runnable, reviewable, and discussable technical anchor for the CNHE concept — not a deployable product.
## Table of Contents



- [Architecture Panorama](#architecture-panorama)

- [Vision & Mission](#vision--mission)

- [Code Quick Look](#code-quick-look)

- [Why CNBE?](#why-cnbe)

- [JEPA Exploration](#jepa-exploration)

- [Cognitive Equity](#cognitive-equity)

- [Key Experiments](#key-experiments)

- [Key Insights I](#key-insights-large-models-vs-small-models)

- [Experimental Limitations & Future Directions](#experimental-limitations--future-directions)

- [Tech Stack](#tech-stack)

- [AI Agent Driven / AI Factory](#ai-agent-driven--ai-factory)

- [Quick Start](#quick-start)

- [Project Structure](#project-structure)

- [Roadmap](#roadmap)

- [How to Contribute](#how-to-contribute)

- [Disclaimer](#disclaimer)

- [License](#license)



---



## Code Quick Look



**Core Idea: Transform Chinese characters into 32-bit integers containing radical, stroke count, and structure type — letting the machine "see" the glyph directly.**



### CJK Character Mode (v6.0 Final)



```

Bit: 31              24 23    19 18    15 14              4  3     0

     +----------------+--------+--------+------------------------+-------+

     |  Radical (8bit)|Stroke(5)|Struct(4)|  Glyph Index (11bit)  | Ext(4)|

     +----------------+--------+--------+------------------------+-------+

```



| Field | Bit Range | Description | Range |

|-------|-----------|-------------|-------|

| Radical | `[31:24]` | 214 Kangxi radicals + 41 extensions | 0-255 |

| Stroke Count | `[23:19]` | Number of strokes | 1-31 |

| Structure Type | `[18:15]` | Structural composition type | 9 types (single/left-right/top-bottom/enclosure, etc.) |

| Glyph Index | `[14:4]` | Intra-group index | 20,902 basic CJK characters |

| Extension | `[3:0]` | Traditional/Simplified, ancient/modern, dialect, reserved flags | Reserved |



### Encoding Examples



| Character | Unicode | CNBE-32 Encoding | Radical (ID) | Stroke Count | Structure Type |

|-----------|---------|-----------------|--------------|--------------|----------------|

| 一 (one) | U+4E00 | `0x01080000` | 一 (1) | 1 | Single (独体) |

| 汉 (Chinese) | U+6C49 | `0x0F288101` | 氵 (water, 15) | 5 | Left-Right (左右) |

| 国 (country) | U+56FD | `0x1F400B0B` | 囗 (enclosure, 31) | 8 | Full Enclosure (全包围) |

| 明 (bright) | U+660E | `0x48400801` | 日 (sun, 72) | 8 | Left-Right (左右) |



---







## Important: This is Not Base32



CNBE-32 is **not** a "Chinese-localized" or "character-replacement" version of Base32.



| Dimension | Base32 | CNBE-32 |

|-----------|--------|---------|

| **Encoding target** | Arbitrary binary data | **97,686 CJK characters themselves** |

| **Code space** | Fixed 32 letters | **Structured 32-bit bitfield** (radical, stroke, structure) |

| **Goal** | Data compression / transmission | **Let machines "understand" character semantics** |

| **Target audience** | Human-readable (transcription) | **AI models, CPU instruction sets, OS kernels** |



**In one sentence**: Base32 turns data "into letters", CNBE-32 turns characters "into semantics".



### Who is it for?



- **AI models**: Structured prior knowledge input (radical=spatial anchor, stroke=discrete feature, structure=spatial relationship)

- **CPU instruction sets**: `cnhe.map` / `cnhe.extract` / `cnhe.cmp` operate at the hardware level

- **OS kernels**: Filenames, paths, system messages natively support CNBE-32 encoding

- **Not recommended**: URL transmission, database primary keys, human transcription (use Base64/Base32)



---



## Why CNBE?



| Dimension | Unicode / UTF-8 | CNBE-32 |

|-----------|-----------------|---------|

| Objective | Character display and exchange | AI understanding and hardware acceleration |

| Encoding Method | Lookup table (Flat ID) | Semantic structuring |

| Machine Cognition | Identifies the character | Understands structural composition |

| AI Compatibility | Learns from data | Provides structural priors |



**10 cross-domain validations passed (incl. LLM LoRA training)**: Linguistics, Ecology, Meteorology, Finance, Biology, Physics, Sociology, Pre-training, Mathematics



---



## JEPA Exploration



CNBE is not a patch for today's Transformers, but foundational infrastructure for tomorrow's JEPA.



Yann LeCun's JEPA emphasizes prediction in representation space — and CNBE provides exactly the most structured representation space:



- **Radical = Spatial Anchor**: Characters sharing the same radical naturally cluster in binary space

- **Stroke Count = Discrete Feature**: Provides fine-grained morphological differentiation

- **Structure = Spatial Relationship**: Left-right, top-bottom, enclosure, etc. directly map to topological relationships



Completed JEPA validations: v9 tree structure prediction + v10 cross-9-domain generalization



> **Cross-domain applicability**: CNBE performs best on multi-dimensional structured temporal data (meteorology, ecology, finance). It may underperform on classification-heavy tasks (sociology, protein structure) or single-variable continuous systems (physics). See [Experimental Limitations](#experimental-limitations--future-directions) for details.



---


## Language Accessibility — Exploratory Perspective

One side observation from this project is that the underlying abstractions of computing (instruction sets, kernel APIs, filesystem paths, debug messages) are overwhelmingly designed around English. While this does not prevent Chinese-speaking developers from being highly proficient, it adds a layer of indirection in certain low-level development contexts.

Whether a Chinese-native binary encoding can meaningfully reduce this indirection is **an open question** that this project explores only incidentally. The primary research vector remains the encoding's impact on machine learning model performance, not human-computer interaction.
## Key Experiments



### Small Model, Big Improvement (v2)



**Hypothesis**: Structured encoding compensates for insufficient small model parameters.

**Method**: Qwen 3.5 0.8B, CNBE vs standard input.



| Input | Accuracy | Improvement |

|-------|----------|-------------|

| Standard input | 48% | -- |

| **CNBE-32** | **87%** | **+81%** |



### CNBE Surpasses Unicode (v6.5.2)



**Hypothesis**: Structured bit fields carry more semantic information than Unicode code points.

**Method**: Gemma 4B Chinese hard tasks.



| Input | Accuracy |

|-------|----------|

| Unicode | 26.1% |

| **CNBE-32** | **43.5%** |



**Conclusion**: A brand-new encoding without prior training outperforms the 30-year standard on first attempt (+17.4 pp).



### Full Chinese Operating System (v8.4)



- Full Chinese Shell (output/get encoding/compare commands)

- Chinese BASIC interpreter (7 keywords)

- Text editor (built-in Tao Te Ching, 205 lines)

- RISC-V custom instructions: `cnhe.map` / `cnhe.extract` / `cnhe.cmp`



> **Note on v8.4**: This is a proof-of-concept (PoC) prototype. The agent-generated code has 9 blocking architectural issues (encoding corruption, page table mismatch, wrong instruction width, unimplemented trap handlers, etc.) and cannot compile without human review. The concept is validated, but the code requires deep human engineering involvement before it can run on QEMU. See [linux_cnbe32_riscv/WHITEPAPER.md](./linux_cnbe32_riscv/WHITEPAPER.md)



### Mathematical Reasoning Foundation (v10.8)



**Method**: TinyGPT on odd/even/prime/sequence reasoning tasks comparing 4 encodings.



| Task | CNBE Loss | OneHot Loss | Winner |

|------|-----------|-------------|--------|

| Odd/Even | 0.3174 | 0.3427 | **CNBE** |

| Prime | 0.3894 | 0.5061 | **CNBE** |

| Sequence | 1.0726 | 1.2344 | **CNBE** |



---



### Complete Experimental Data (v1~v10)



<details>

<summary><b>Click to expand v1~v10 core experiment overview</b></summary>



| Version | Validation Dimension | Model / Platform | Core Metric | Key Conclusion |

| :---: | :--- | :--- | :--- | :--- |

| **v1** | Zero-shot single character understanding | Qwen 0.8B | 200 characters, **100%**\* effective | Encoding is inherently semantically interpretable |

| **v2** | Small model sentence understanding | Qwen 0.8B | 48% **→ 87%** (**+81%**) | Structured encoding provides significant compensation for small models |

| **v3** | Annotation format optimization | Qwen 0.8B | Character-by-character full annotation **87%** effective | Optimal format: character-by-character full annotation |

| **v4** | Long text (paper-level) | Qwen 0.8B | 90.9% **→ 100%**\* | Effective in long-text scenarios, eliminates ambiguity |

| **v5** | Multi-model horizontal comparison | 7 models | <1B: +81%; 1-7B: +9~17%; >7B: ~0% | **Diminishing marginal returns** |

| **v6** | Unicode hard task comparison | Gemma 4B | Unicode 26.1% **vs** **CNBE 43.5%** | **CNBE > Unicode** (+17.4 pp) |

| **v7** | RISC-V hardware implementation | C / QEMU / Spike / FPGA | x86 0.8 ns → FPGA **1 Cycle** | Complete hardware path closed-loop |

| **v8** | Full Chinese operating system | RISC-V QEMU | Chinese Shell + BASIC + Tao Te Ching editor | Encoding can seamlessly integrate into OS underlying layer |

| **v9** | JEPA tree structure prediction | JEPA architecture | Error **0.0899 → 0.000001** | Extremely strong high-noise temporal feature extraction |

| **v10** | Cross-9-domain generalization | Multi-domain | Mathematics wins; typhoon error **−19%** | Effective across mathematics/physics/biology/finance and other domains |



</details>



<details>

<summary><b>Click to expand v1~v10 detailed experimental data</b></summary>



| Version | Sub-item / Task | Test Environment | Specific Data Metrics | Conclusion / Notes |

| :---: | :--- | :--- | :--- | :--- |

| **v1** | Single character radical/stroke/structure extraction | Qwen 0.8B | 200 Chinese characters, **100%** zero-shot effective | Proves encoding space IS semantic space |

| **v2** | Chinese sentence understanding | Qwen 0.8B | Text input 48% → CNBE **87%** | Accuracy improvement 39 pp |

| **v3** | Encoding format ablation experiment | Qwen 0.8B | Character-by-character 87% > segmented 60% > compact 50% | Optimal: `中(丨,4 strokes, single)` |

| **v4** | Paper-level semantic understanding | Qwen 0.8B | 90.9% → **100%**\* | Complements small model long-context reasoning shortcomings |

| **v5a-5.9** | 7-model horizontal comparison | 0.8B~20B | Domestic 2B **90%**; 8B+ approaches 0 | Less compute power = more important structural priors |

| **v6.3-6.5** | Numerical format optimization | Qwen 0.8B | **Format F (bare numbers)** optimal | Hardware recommends bare number input |

| **v6.5.2** | CNBE vs Unicode | Gemma 4B | Unicode 26.1% **vs** CNBE **43.5%** | Outperforms thirty-year industry standard on first attempt |

| **v7.0** | C language benchmark | x86-64 | Single lookup **0.8 ns** | Software performance baseline established |

| **v7.0.1** | RISC-V cross-compilation | QEMU | Single lookup 2.5 ns | Validates RISC-V portability |

| **v7.1.1** | Instruction integration | Spike | `map`(2 cycles) / `extract`(1) / `cmp`(3) | Three Custom-0 instruction behaviors verified |

| **v7.2** | FPGA logic synthesis | Verilog+BRAM | **Single cycle** lookup complete | 81.6 KB table entries fit BRAM resources |

| **v8.4** | Full Chinese system | RISC-V QEMU | Shell commands + BASIC 7 keywords + Tao Te Ching | "Full Chinese computing" feasibility validated |

| **v9.0** | Tree growth JEPA | JEPA | CNBE **86%** better than Raw | Structured encoding improves abstract representation |

| **v9.1** | Typhoon lifecycle | JEPA | 0.089981 → **0.000001** | Error reduced by 4 orders of magnitude |

| **v10.3** | Typhoon Bavi path | Meteorological model | 216 km → **174 km** | Actual path prediction accuracy improved 19% |

| **v10.4** | Protein Q3 structure | Bioinformatics | OH 44.6% vs CNBE 41.0% | Slightly below OH; biological sequence still has optimization room |

| **v10.5** | Black hole gravitational field | Physics simulation | R² **0.60-0.77** | Good performance in physics field simulation |

| **v10.7** | TinyGPT frozen embedding | TinyGPT | Learned 1.3653 vs CNBE 1.4568 | Frozen embedding performance close to learned embedding |

| **v10.8** | Mathematical reasoning foundation | TinyGPT | Odd/Even(0.3174<0.3427) Prime(0.3894<0.5061) Sequence(1.07<1.23) | Universally better than One-Hot |

| **LLM** | CNBE knowledge LoRA fine-tuning | Qwen3.5-0.8B | 5000 steps, loss **0.6424**, 500-steps 0.7524 | Knowledge injection feasible, edge deployment validated |





</details>



> \* 100% refers to model task performance on specific test sets. See individual whitepapers for methodology.



### Complete Evidence Chain Logic Closure



| Stage | Corresponding Version | Logical Role |

| :--- | :--- | :--- |

| **Semantic Validity** | v1 ~ v4 | Prove encoding itself contains semantics |

| **Comparative Superiority** | v5 ~ v6 | Prove encoding outperforms Unicode |

| **Hardware Implementability** | v7 | Prove from software to FPGA is feasible |

| **System-level Compatibility** | v8 | Prove encoding can support complete OS ecosystem |

| **Cross-domain Generalization** | v9 ~ v10 | Prove equally effective in physics/biology/finance and other domains |



Complete experimental data → [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md)



---



## Key Insights: Large Models vs Small Models



Why do 8B+ large models show diminishing returns (~0%) from CNBE, while 0.8B small models achieve massive +81% improvement?



- **Large Model Brute Force Aesthetics**: Massive parameters can implicitly memorize Unicode through brute-force training, masking the structural flaws of the encoding

- **Small Model Structural Priors**: On compute-constrained edge devices, CNBE transforms glyph structure directly into computational priors



This is the breakthrough path for edge-side AI processing of Chinese.



> ## Key Insights II: AI Agent Full-Stack OS Translation

>

> — Porting Linux 0.01 from x86 to RISC-V + CNBE-32 by GPT-5/Codex Agent

>

> - **The agent wrote genuinely complex systems-level code**: 49 C files, 6 assembly files, 36 headers — including a complete CNBE-32 runtime, Chinese BASIC interpreter (1748 lines, 16 keywords) and a Chinese bytecode compiler (1315 lines, 27 instructions). The code is substantive and structurally complete.

> - **But the agent does not test its own code**: 9 blocking architectural issues were found (encoding corruption, Sv32/Sv39 page table mismatch, wrong instruction width, unimplemented trap handlers, etc.). The code cannot compile without human review.

> - **A 'fully Chinese OS' is both within reach and far away**: The proof of concept exists, but making the code actually run on QEMU still requires deep human engineer involvement.

>

> This is the first complete attempt by an AI Agent at systems-level software translation — demonstrating capability boundaries while also revealing current limitations. Full analysis → [linux_cnbe32_riscv/WHITEPAPER.md](./linux_cnbe32_riscv/WHITEPAPER.md)



> ## Key Insights III: CNBE Encoding Knowledge LoRA Fine-Tuning

>

> — Injecting CNBE-32 encoding knowledge into Qwen3.5-0.8B via LoRA

>

> - **LoRA knowledge injection works**: 500 steps (22 min) + 5000 steps (4.14 h) with 25K diverse Chat Template data, loss from 0.7524 → **0.6424** (↓14.6%), augmentation artifacts eliminated

> - **Model understands encoding concepts**: After fine-tuning, the model recognizes character radicals, stroke counts, and structure types, outputting CNBE-32 encoded information

> - **Minimal GPU requirements**: RTX 4060 Ti (8GB) handles the entire pipeline, with peak memory usage of only 1.5GB

> - **Edge deployment validated**: For the first time, CNBE-32 advances from inference-level semantic validation to training-level knowledge injection

> - **Complete cross-domain chain**: From linguistics to finance to physics to biology to LLM training, CNBE's structured encoding is validated across encoding, hardware, OS, cross-domain prediction, and model fine-tuning

>

> Full methodology → [cnbe-llm training(demo)/](<./cnbe-llm training(demo)/>)







---




## 🗺️ Relationship to the 2035 Vision

This project is positioned at the intersection of three timelines:

| Timeline | Scope | Relevance to CNBE-32 |
| :--- | :--- | :--- |
| **Short-term (2026)** | Academic validation | Current PoC demonstrates encoding feasibility on <1B models and RISC-V simulation |
| **Medium-term (2028-2030)** | Engineering maturation | Requires OS kernel fixes, FPGA board-level validation, third-party reproduction |
| **Long-term (2035)** | Strategic deployment | Aligns with the "National Cultural Big Data System" and "Digital China 2035" vision |

The paper *Language Sovereignty and Digital Governance* argues that by 2035, a Chinese native AI governance system will gradually mature, contributing to global digital governance. CNBE-32 contributes to this vision at the **encoding layer** — the foundation upon which all other layers (data, algorithms, applications) are built.

**This project does not claim to have achieved the 2035 vision.** It provides a **runnable starting point** for academic discussion, technical iteration, and community collaboration.
## Experimental Limitations & Future Directions



> **We have faithfully documented failures and limitations in all experiments. The following are known boundaries disclosed directly in this README.**



### Known Limitations



| Experiment | Limitation | Future Direction |

|------------|------------|------------------|

| v5/v6 (LLM validation) | Some models (DeepSeek 8B / GPT-OSS 20B) showed empty responses or insufficient Chinese capability | Focus on Chinese-friendly small models like Qwen/Gemma |

| v6.5.3 (Hard task 0.8B) | Overall only 12.5%, CNBE and Unicode showed no difference | 0.8B model capability boundary; requires larger model validation |

| v9.0 (Tree growth) | Simulated environment, not real climate/economic data | Validate on real temporal data |

| v10.0/v10.1 (Financial backtesting) | A-share high-frequency trading costs (0.14%/trade) consumed all strategy returns; break-even point not reached | Pivot to low-frequency strategies (daily/weekly) to unlock predictive value |

| v10.4 (Protein) | Used simplified single-residue method, not standard sliding window; first contact with 30-year domain standard gap of 3.6 pp | Sliding window + CB513 dataset complete experiment |

| v10.5 (Black hole) | Single-variable input scenario (only r/Rs), continuous value KNN naturally precise; CNBE quantization introduces error | Multi-dimensional input scenario (with observation noise) validation |

| v10.6 (Sociology) | **CNBE inferior to One-hot in strong classification feature scenarios** (MSE 0.0124 vs OneHot 0.0019) | Field weighting, hierarchical encoding optimization |

| v10.7 (Pre-training) | Task too simple (13 token vocabulary), difference not statistically significant | Large-scale corpus, larger model validation |



### Applicability Boundaries (Based on All Experimental Data)



| Scenario Type | CNBE Performance | Typical Domains | Reason |

|---------------|:----------------:|-----------------|--------|

| Multi-dimensional continuous value + structured temporal | ✅ Significantly better than baseline | Meteorology, ecology, finance, mathematics | Bit-field structured encoding naturally matches |

| Strong classification features | ❌ Inferior to One-hot | Sociology (8 regions + 4 time periods) | Bit-field mixed encoding cannot distinguish classification field weights |

| Single-variable deterministic systems | ⚠️ Equal to Raw | Physics (gravitational field) | Continuous value single-variable scenario Raw is optimal |

| Zero-shot unfamiliar domains | ⚠️ Close to domain standard | Biology (protein) | First attempt approaches 30-year optimized standard |

| Pattern recognition tasks | ✅ Universally better than One-hot | Mathematical reasoning | Structured encoding matches pattern recognition |



---



## Tech Stack



```

Application Layer: Chinese BASIC interpreter + Text Editor + Tao Te Ching

System Layer: Full Chinese Shell + CNBE Runtime (map/extract/cmp)

Hardware Layer: RISC-V 1GHz + 1GB RAM (QEMU + Spike)

Instruction Layer: cnhe.map / cnhe.extract / cnhe.cmp

Encoding Layer: 32-bit CJK Structured Bit Fields (Radical/Stroke/Structure)

```



---


## AI-Assisted Development: A Methodological Specimen

This project was developed with assistance from AI systems (Codex / GPT-5 architecture). **This is not a shortcut — it is a deliberate research methodology.**

| Past Approach | Current Approach (2026) |
| :--- | :--- |
| Manual Chinese character annotation by linguists | AI-assisted automated annotation |
| Manual full-stack validation by top-tier teams | LLM-assisted code generation + validation |
| Isolated team development | Open source community exploration |

AI-assisted development enabled rapid prototyping and iteration across five traditionally siloed domains: NLP, encoding databases, instruction set design, OS kernels, and hardware simulation.

**However, all AI-generated code and experiments must be reviewed by human engineers before use** — this is particularly important for the RISC-V hardware patches and encoding database generation, which may contain subtle issues not caught by automated tests.

The v8.4 OS kernel code is a case in point: the agent-generated code contained known architectural issues and could not compile without human review. The encoding concept was validated, but the system-level code required substantial human engineering intervention.

**This project thus serves a dual purpose:**
1. **Validating CNHE theory** — demonstrating the encoding concept is technically feasible
2. **Documenting the boundaries of AI-assisted development** — recording, at this point in 2026, where AI-generated code succeeds and where it fails

Agents have participated in: [encoding design v1] [experiment result analysis v2] [hardware link v7] [OS framework v8] [cross-domain experiment v9-v10]
## Quick Start



### Environment Requirements

- Python 3.8+

- numpy, torch, scikit-learn (for experiment reproduction)



### Install Python SDK



```bash

pip install numpy torch scikit-learn

```



### Usage Example



```python

import sys; sys.path.insert(0, 'src')

from cnbe32 import encode_cnbe, hamming_distance



code_ming = encode_cnbe(72, 8, 1)   # 明 (bright) = 日(sun, 72) + 8 strokes + left-right structure

code_an  = encode_cnbe(72, 9, 1)   # 暗 (dark) = 日(sun, 72) + 9 strokes + left-right structure

print(hamming_distance(code_ming, code_an))

```



### Run RISC-V Simulator



```bash

cd hardware/simulator

gcc -o cnhe_sim cnhe_sim.c -Wall -O2 && ./cnhe_sim

```



### Launch Full Chinese Operating System (QEMU)



```bash

# Ubuntu dependencies

sudo apt-get install -y gcc-riscv64-linux-gnu qemu-system-misc



cd v84_riscv_os_full

make all && make run

```



### Reproduce Experiments



```bash

cd v10_8_math_reasoning && python run_v108.py

cd v10_3_typhoon && python v10_3_typhoon.py

```



---







## Application Scenarios



CNBE-32 is designed for **AI-era Chinese computing infrastructure**, not as a general-purpose encoding tool.



| Scenario | Suitability | Description |

|----------|:-----------:|-------------|

| AI model structured input | **Recommended** | Provides radical/stroke/structure priors, improves small model comprehension |

| RISC-V hardware acceleration | **Recommended** | Custom instructions operate directly on encoding bitfields |

| Chinese-native OS | **Recommended** | Native support for filenames, paths, system messages |

| Chinese compiler/BASIC | **Recommended** | Direct encoding operations at the language level |

| Data compression/obfuscation | Not recommended | Semantic encoding, not compression |

| URL transmission | Not recommended | Characters broken by %-encoding in URLs |

| Human transcription | Not recommended | Visually similar characters cause errors |

| Database primary keys | Use with caution | 32-bit integers are storable but CNBE is not a unique identifier |



---



## Project Structure



```

CNBE-32-Chinese-Native-Binary-Encoding/

|-- docs/specification/      # Encoding specification

|-- docs/EXPERIMENTS.md      # Experiment overview

|-- docs/VISION.md           # Strategic vision

|-- src/cnbe32/              # Python SDK

|-- include/cnbe32.h         # C header file

|-- data/                    # Encoding database

|-- tests/                   # Test suite

|-- tools/                   # Development tools

|-- bindings/rust/           # Rust bindings

|-- hardware/                # RISC-V simulator

|-- v9_jepa_tree/            # JEPA experiments (v9)

|-- v10_5~v10_8/             # Cross-domain experiments (v10)

|-- v84_riscv_os_full/       # Chinese OS prototype

|-- results/                 # White papers (41 documents)

|-- LICENSE                  # Mulan License

```



---




## Changelog

### v1.0.1 (2026-07-09) — Code Quality & Architecture Fixes

- **`CNBE32` class**: `__init__` now properly initializes `_table`. `encode()` raises `CNBECharNotInTableError` instead of silently falling back to a zero array.
- **`encoders.py`**: All `encode()` methods reformatted for readability. `OneHotEncoder` now validates index bounds.
- **Hardcoded paths fixed**: `cnbe_simulator.py`, `generate_cnbe_table.py`, `cnbe_riscv_sim.py` now use environment variables (`CNBE_TABLE_DIR`, `CNBE_SOURCE_XLSX`) instead of hardcoded desktop paths.
- **`.gitignore`**: Added rules for large binary artifacts (`*.db`, `*.xlsx`, `*.docx`, `*.json.gz`).
- **Version sync**: `__init__.py` version updated from `0.4.0` to `1.0.1` to match `pyproject.toml`.
- **CI**: Added `ruff check src/` to the CI pipeline. Added `[tool.ruff]` configuration.
## Roadmap



| Phase | Status | Content |

|-------|--------|---------|

| Encoding & semantic validation | Completed | v1-v6 CJK encoding design |

| Hardware & system | Completed | v7-v8 RISC-V + Chinese OS |

| Complex prediction validation | Completed | v9-v10 9-domain validation |

| AI compiler | Planned | Chinese natural language → machine code |

| Edge AI integration | Planned | Edge AI default standard |

| Ecosystem collaboration | Vision | Open source community + industry standards |



---


## How to Contribute

### Current Directions Most Needing Community Support

- **Fix RISC-V kernel port defects**: The linux-cnbe32-riscv kernel has known C symbol naming convention issues that prevent linking. Help resolving these is the single most impactful contribution.
- **Complete experimental baseline reproduction**: Establish independently reproducible evaluation pipelines for the v2~v10 experiments.
- **Hardware verification**: FPGA board-level testing of the Verilog RTL modules.
- **Encoder library cleanup**: Improve documentation, add type hints, and increase test coverage.

| Barrier Level | Direction |
|---------------|-----------|
| Low | Documentation, test cases, encoding dictionary improvements |
| Medium | Python SDK enhancements, experiment reproduction, cross-platform CI |
| High | RISC-V kernel debugging, FPGA verification, LLM adaptation |

See [CONTRIBUTING.md](CONTRIBUTING.md) for details
## Project Status & Positioning

### 1. This is an experimental research project, not a usable product

CNBE-32 is at a **very early proof-of-concept (PoC)** stage. The project's RISC-V instruction extension and operating system adaptation code contain known architectural defects and **cannot currently compile or run on actual hardware**. All experimental data is produced under controlled simulation environments and carries **no guarantees of production-level usability, stability, or security**. Do not use any component of this project in production systems.

### 2. The specific research question

Modern AI systems process Chinese text through tokenization (subword splitting), which discards the visual structure of Chinese characters (radicals, strokes, spatial composition). This project investigates a narrow empirical question:

> **Can explicitly encoding radical, stroke count, and structure type as a 32-bit bitfield provide small language models (<1B parameters) with a more effective inductive bias than flat Unicode codepoints?**

This is **not** a Unicode replacement, **not** a "domestic operating system," **not** a general solution for large language models (>7B). It is simply an empirical tool for testing the above hypothesis.

### 3. References to broader context are background, not goals

References to "Digital China" or "Chinese-native computing" in this document are used solely to illustrate the **inspiration and motivation** for this research direction. They do **not** imply that this project has achieved any level of practical relevance to those strategic goals, nor that the maintainers have the capacity or intent to realize them.

### 4. Known hard limitations

| Limitation | Detail |
|------------|--------|
| **Scale failure** | CNBE benefits are clearly observed in small models (<1B) but approach zero in large models (>7B). The encoding does **not** exhibit clear scaling laws. |
| **Hardware unverified** | RISC-V RTL designs have only completed functional simulation; **no FPGA board-level testing or tape-out**. |
| **Cross-domain results are preliminary** | Experiments in meteorology, finance, and other domains use limited simulation environments. **Do not treat as real-world predictions.** |
| **Reproducibility incomplete** | Experimental scripts and core encoding libraries require further cleanup. Independent third-party reproduction has not been completed. |

### 5. Who is this for?

| Audience | Suitability |
|----------|-------------|
| ✅ **Academic researchers** in NLP, linguistics, or computer architecture interested in non-Unicode Chinese encoding as a discussion baseline | Appropriate |
| ✅ **Experimental AI developers** willing to test structured input features on small models (<1B) | Appropriate |
| ❌ **Production developers** seeking stable Chinese encoding or OS infrastructure | **Not suitable in current state** |

### 6. To potential contributors

Rather than conceptual support, the project's most pressing needs are technical contributions that address these specific issues:

- Fix the known architectural defects in the RISC-V Spike/QEMU adaptation (see [WHITEPAPER.md](WHITEPAPER.md) for details)
- Complete Verilog module timing optimization and FPGA board-level verification
- Establish independently reproducible experimental baselines

### 7. Academic Positioning

CNBE-32 is an **academic research prototype**, not a commercial product.

- **It is a technical validation of the CNHE theory** proposed in the paper *Language Sovereignty and Digital Governance*, not a production-ready encoding standard.
- **It is a product of AI-assisted research methodology**, documenting both the potential and the limitations of current AI code generation capabilities.
- **It is positioned for the 2035 long-term vision**, not for current deployment in any production environment.

All experimental results reported in this README are based on controlled research environments. **They do not constitute investment advice, operational recommendations, or policy proposals.**
## License



**Mulan Permissive Software License v2 (Mulan PSL v2)**



[![License](https://img.shields.io/badge/License-MulanPSL2-blue.svg)](http://license.coscl.org.cn/MulanPSL2)



---



**Let Chinese speakers enter the AI era through their native language.**



From the "Digital China 2035" vision to AI Agent era engineering practice.



**Born for Chinese AI ecosystem — from encoding to hardware, from single character to operating system.**



[GitHub](https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding)











