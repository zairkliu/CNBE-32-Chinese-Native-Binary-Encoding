# CNBE-32 Mathematical Structure

**Role:** Research mathematics for the CNBE-32 encoding — a self-contained presentation of every formal object the project currently defines.

**Verification status:** All formula groups below have reference implementations with numerical property checks (identity, symmetry, bounds, closure, permutation composition). These are **research definitions**: they do not certify the linguistic correctness of any bitfield, and they do not by themselves demonstrate task-level gains on retrieval, geometry, routing, or representation benchmarks. Task value still requires independent external review under the project's evidence gates.

---

## 1. The 32-bit word and its bitfield layout

A CNBE-32 code is an unsigned 32-bit integer:

$$
c \in \{0, 1, \ldots, 2^{32}-1\}.
$$

Five fields partition the word, LSB-first:

```text
31              24 23        19 18     15 14                 4 3        0
┌────────────────┬────────────┬─────────┬─────────────────────┬──────────┐
│ Radical/Radix  │  Stroke    │ Struct  │     Glyph Index     │   Ext    │
│     8 bits     │  5 bits    │ 4 bits  │       11 bits       │  4 bits  │
└────────────────┴────────────┴─────────┴─────────────────────┴──────────┘
```

| Field | Bits | Width $d_k$ | Mask $M_k$ | Shift $S_k$ |
|---|---:|---:|---|---:|
| Radical / Radix | 24–31 | 8 | `0xFF000000` | 24 |
| Stroke | 19–23 | 5 | `0x00F80000` | 19 |
| Structure | 15–18 | 4 | `0x00078000` | 15 |
| Glyph Index | 4–14 | 11 | `0x00007FF0` | 4 |
| Extension | 0–3 | 4 | `0x0000000F` | 0 |

---

## 2. Core operators

### 2.1 Field extraction

The $k$-th field is recovered from the word by mask-and-shift:

$$
\mathrm{Extract}(c, M_k, S_k) = (c \land M_k) \gg S_k
$$

This is the hardware-friendly primitive: one AND, one shift, no branching. It is the only operation every higher layer in this document is built from.

### 2.2 Binary vector and its inverse

The LSB-first binary vector of the word:

$$
\Phi(c) = [b_0, b_1, \ldots, b_{31}]^{\mathsf{T}}, \qquad b_i = \left\lfloor \frac{c}{2^i} \right\rfloor \bmod 2
$$

with exact inverse:

$$
c = \sum_{i=0}^{31} \Phi(c)_i \cdot 2^i
$$

The representation layer is **reversible**: it round-trips losslessly over 6,568 frozen P0 records and 11 cross-language golden vectors. Reversibility is a property of the *carrier* — it does not make adjacent bits or numeric field codes linguistic distances.

---

## 3. Weighted morphological distance

The project-level similarity measure between two codes is a field-wise normalized Hamming distance with research weights:

$$
\mathcal{D}_{\mathrm{morph}}(c_1, c_2) = \sum_{k \in K} w_k \cdot \frac{\mathrm{POPCNT}\Big( (c_1 \land M_k) \oplus (c_2 \land M_k) \Big)}{d_k}
$$

where $\oplus$ is bitwise XOR, $\mathrm{POPCNT}(\cdot)$ is the hardware population-count instruction, and $d_k$ is the field width from §1. The supplied research weights:

$$
(w_{\mathrm{radix}},\ w_{\mathrm{stroke}},\ w_{\mathrm{struct}},\ w_{\mathrm{index}},\ w_{\mathrm{ext}}) = (0.4,\ 0.2,\ 0.2,\ 0.1,\ 0.1), \qquad \sum_{k} w_k = 1
$$

**Verified numerical properties:** identity of indiscernibles, symmetry, $[0, 1]$ boundedness, and field-isolation increments — a difference confined to field $k$ contributes exactly $w_k$ times the fraction of bits that differ in that field.

**Explicit caveat:** the weights have no independent linguistic-task validation. In particular, `index` and `ext` are not thereby established as morphology evidence. $\mathcal{D}_{\mathrm{morph}}$ is a *computable hypothesis* about morphological similarity, not a certified one.

---

## 4. Candidate hyperbolic layer (Poincaré ball)

Chinese characters form hierarchy-heavy structures (character → component → stroke), which motivates a hyperbolic candidate space:

$$
\mathbb{B}^{d} = \{ \mathbf{x} \in \mathbb{R}^{d} : \| \mathbf{x} \| < 1 \}
$$

### 4.1 Geodesic distance

$$
d_{\mathbb{B}}(\mathbf{u}, \mathbf{v}) = \mathrm{arcosh} \left( 1 + 2 \, \frac{\| \mathbf{u} - \mathbf{v} \|^{2}}{(1 - \| \mathbf{u} \|^{2})(1 - \| \mathbf{v} \|^{2})} \right)
$$

### 4.2 Möbius addition

$$
\mathbf{u} \oplus_{\mathbb{B}} \mathbf{v} = \frac{(1 + 2 \langle \mathbf{u}, \mathbf{v} \rangle + \| \mathbf{v} \|^{2}) \, \mathbf{u} + (1 - \| \mathbf{u} \|^{2}) \, \mathbf{v}}{1 + 2 \langle \mathbf{u}, \mathbf{v} \rangle + \| \mathbf{u} \|^{2} \| \mathbf{v} \|^{2}}
$$

### 4.3 Origin exponential map

$$
\exp_{\mathbf{0}}(\mathbf{v}) = \tanh(\| \mathbf{v} \|) \, \frac{\mathbf{v}}{\| \mathbf{v} \|}
$$

with $\exp_{\mathbf{0}}(\mathbf{0}) = \mathbf{0}$ by continuous extension.

### 4.4 Character composition

A character's embedding is the Möbius composition of its three structural field embeddings:

$$
\mathbf{z}_c = \mathbf{e}_{\mathrm{radix}} \oplus_{\mathbb{B}} \mathbf{e}_{\mathrm{struct}} \oplus_{\mathbb{B}} \mathbf{e}_{\mathrm{stroke}}
$$

### 4.5 Geometry-alignment loss

The hyperbolic geometry is trained to mirror the morphological distance of §3:

$$
\mathcal{L}_{\mathrm{hyperbolic}} = \frac{1}{N^{2}} \sum_{i=1}^{N} \sum_{j=1}^{N} \left| d_{\mathbb{B}}(\mathbf{z}_{c_i}, \mathbf{z}_{c_j}) - \gamma \cdot \mathcal{D}_{\mathrm{morph}}(c_i, c_j) \right|^{2}
$$

**Verified numerical properties:** ball domain and closure under $\oplus_{\mathbb{B}}$, additive identity at $\mathbf{0}$, symmetry of $d_{\mathbb{B}}$, sampled triangle inequality, and finite non-negative loss.

**Explicit caveat:** reference inputs are deterministic synthetic tangent fixtures — not learned embeddings, and not evidence that hyperbolic geometry beats Euclidean baselines on any task.

---

## 5. Candidate bitwise MoE router

The radix field can act as a zero-cost routing hint for a mixture-of-experts layer with $E$ experts:

$$
e_{\mathrm{pred}}(c) = \mathrm{Extract}(c, \text{0xFF000000}, 24) \bmod E
$$

combined with a learned gate by interpolation:

$$
P(e \mid x, c) = (1 - \alpha) \cdot \mathrm{Softmax}_{e}(\mathbf{W}_g \mathbf{h}_x) + \alpha \cdot \delta \big( e,\ e_{\mathrm{pred}}(c) \big)
$$

**Verified numerical properties:** routing range $[0, E)$, modulo consistency, non-negative normalized probabilities, and correct $\alpha = 0$ / $\alpha = 1$ endpoints.

**Explicit caveat:** no latency, load-balance, or quality gains are demonstrated. This is a routing *mechanism definition*, not a benchmark result.

---

## 6. Candidate hyperdimensional (HDC/VSA) representation

For dimension $D = 10{,}000$ and field basis vectors $\mathbf{B}_k \in \{-1, +1\}^{D}$ derived deterministically from SHA-256:

**Cyclic permutation (binding by position):**

$$
\Pi^{p}([v_0, v_1, \ldots, v_{D-1}]) = [v_{D-p}, \ldots, v_{D-1}, v_0, \ldots, v_{D-p-1}]
$$

**Bundled character hypervector** — each field's basis is permuted by that field's extracted value, then superposed:

$$
\mathbf{H}(c) = \mathrm{sign} \left( \sum_{k \in K} \Pi^{\mathrm{Extract}(c, M_k, S_k)}(\mathbf{B}_k) \right)
$$

with the fixed convention $\mathrm{sign}(0) = +1$.

**Similarity:**

$$
\mathrm{Sim}_{\mathrm{HDC}}(\mathbf{H}_1, \mathbf{H}_2) = \frac{\mathbf{H}_1 \cdot \mathbf{H}_2}{D}
$$

**Verified numerical properties:** permutation composition ($\Pi^{p} \circ \Pi^{q} = \Pi^{p+q}$), output range, self-similarity equal to $1$, symmetry, and $[-1, 1]$ boundedness.

**Explicit caveat:** task quality, memory, and latency benefits are unverified. Basis vectors are reproducible fixtures, not learned representations.

---

## 7. Verification status matrix

| Formula group | Definition frozen | Numerical property tests | Linguistic validation | Task-level benchmark |
|---|:---:|:---:|:---:|:---:|
| §2 Bitfields, $\mathrm{Extract}$, $\Phi$ | ✅ | ✅ reversibility (6,568 P0 records, 11 golden vectors) | ❌ not claimed | n/a |
| §3 $\mathcal{D}_{\mathrm{morph}}$ | ✅ | ✅ identity / symmetry / bounds / field isolation | ❌ weights unvalidated | ❌ |
| §4 Poincaré layer | ✅ | ✅ domain / closure / identity / symmetry / sampled triangle inequality | ❌ | ❌ synthetic fixtures only |
| §5 Bitwise MoE router | ✅ | ✅ range / modulo / normalization / endpoints | ❌ | ❌ |
| §6 HDC/VSA representation | ✅ | ✅ composition / range / self-similarity / bounds | ❌ | ❌ |

Passing mathematics does not lift the scientific gate. Retrieval, geometry, routing, and HDC task claims remain gated on the P1 external-review method: row-level source confirmation, independently reviewed negatives, and frozen candidate pools.

---

## 8. Boundaries

1. **Unicode remains the compatibility identity.** Every formula here operates on the CNBE-32 carrier; none of it replaces or reinterprets Unicode codepoints.
2. **Fields are evidence-gated, not math-gated.** A formula computing over the `radix` field does not make the field's value linguistically correct — that authority comes only from the standards-aligned evidence workflow (8105 national-standard core, GF/GB/GG sources, human review state).
3. **Candidate layers are proposals.** The hyperbolic, MoE, and HDC layers are candidate computational structures with verified numerical hygiene. None is a validated model component.
4. **No fabricated validation.** Where a property is not tested, this document says so. Where a test uses synthetic fixtures, it says so.

---

## See also

- [Repository README](../README.md) — project status, coverage terminology, and evidence levels
- [CNBE-32 Formal Mathematical Specification](./specification/CNBE_FORMAL_MATHEMATICAL_SPECIFICATION.md) — terse reference form of the same 13 formulas（[中文版](./specification/CNBE_FORMAL_MATHEMATICAL_SPECIFICATION_ZH.md)）
- [Specification directory](./specification/) — bit layout, architecture, and validation notes
- [CNBE Research Position Statement](./CNBE_RESEARCH_POSITION_STATEMENT.md) — research framing and reproducibility path

**License:** MulanPSL-2.0, same as the repository.
