# CNBE-32 Formal Mathematical Specification

**Role:** Research mathematics, not a national language-writing standard or a source of runtime-field authority.
**Verification:** All 13 supplied formulas have reference mathematical or numerical property checks; task value still requires independent external review.
**Chinese version:** [CNBE-32 形态计算形式化数学说明](CNBE_FORMAL_MATHEMATICAL_SPECIFICATION_ZH.md)
**Companion presentation:** [CNBE-32 Mathematical Structure](../CNBE32_MATHEMATICAL_STRUCTURE.md)

## 1. Bitfields and Binary Vector

For an unsigned 32-bit CNBE word:

$$
c \in \{0, 1, \ldots, 2^{32}-1\}.
$$

The $k$-th field is extracted by its mask $M_k$ and shift $S_k$:

$$
\mathrm{Extract}(c, M_k, S_k) = (c \land M_k) \gg S_k
$$

The LSB-first binary vector is:

$$
\Phi(c) = [b_0, b_1, \ldots, b_{31}]^{\mathsf{T}}, \qquad b_i = \left\lfloor \frac{c}{2^i} \right\rfloor \bmod 2
$$

Its inverse is:

$$
c = \sum_{i=0}^{31} \Phi(c)_i \cdot 2^i
$$

The representation layer is reversible over 6,568 frozen P0 records and 11 golden vectors. It does not make adjacent bits or numeric field codes linguistic distances.

## 2. Weighted Morphological Hamming Distance

$$
\mathcal{D}_{\mathrm{morph}}(c_1, c_2) = \sum_{k \in K} w_k \cdot \frac{\mathrm{POPCNT}\Big( (c_1 \land M_k) \oplus (c_2 \land M_k) \Big)}{d_k}
$$

Here $d_k$ is field width, $\oplus$ is XOR, and $\mathrm{POPCNT}$ counts set bits. The supplied research weights are:

$$
(w_{\mathrm{radix}},\ w_{\mathrm{stroke}},\ w_{\mathrm{struct}},\ w_{\mathrm{index}},\ w_{\mathrm{ext}}) = (0.4,\ 0.2,\ 0.2,\ 0.1,\ 0.1)
$$

The reference implementation verifies identity, symmetry, $[0, 1]$ bounds, and field-isolation increments. The weights have no independent linguistic-task validation; in particular, `index` and `ext` are not thereby established as morphology evidence.

## 3. Candidate Poincaré Model

$$
\mathbb{B}^{d} = \{ \mathbf{x} \in \mathbb{R}^{d} : \| \mathbf{x} \| < 1 \}
$$

### 3.1 Geodesic Distance

$$
d_{\mathbb{B}}(\mathbf{u}, \mathbf{v}) = \mathrm{arcosh} \left( 1 + 2 \, \frac{\| \mathbf{u} - \mathbf{v} \|^{2}}{(1 - \| \mathbf{u} \|^{2})(1 - \| \mathbf{v} \|^{2})} \right)
$$

### 3.2 Möbius Addition

$$
\mathbf{u} \oplus_{\mathbb{B}} \mathbf{v} = \frac{(1 + 2 \langle \mathbf{u}, \mathbf{v} \rangle + \| \mathbf{v} \|^{2}) \, \mathbf{u} + (1 - \| \mathbf{u} \|^{2}) \, \mathbf{v}}{1 + 2 \langle \mathbf{u}, \mathbf{v} \rangle + \| \mathbf{u} \|^{2} \| \mathbf{v} \|^{2}}
$$

### 3.3 Origin Exponential Map

$$
\exp_{\mathbf{0}}(\mathbf{v}) = \tanh(\| \mathbf{v} \|) \, \frac{\mathbf{v}}{\| \mathbf{v} \|}
$$

The reference returns $\mathbf{0}$ by continuous extension when $\mathbf{v} = \mathbf{0}$.

### 3.4 Character Composition

$$
\mathbf{z}_c = \mathbf{e}_{\mathrm{radix}} \oplus_{\mathbb{B}} \mathbf{e}_{\mathrm{struct}} \oplus_{\mathbb{B}} \mathbf{e}_{\mathrm{stroke}}
$$

### 3.5 Alignment Loss

$$
\mathcal{L}_{\mathrm{hyperbolic}} = \frac{1}{N^{2}} \sum_{i=1}^{N} \sum_{j=1}^{N} \left| d_{\mathbb{B}}(\mathbf{z}_{c_i}, \mathbf{z}_{c_j}) - \gamma \cdot \mathcal{D}_{\mathrm{morph}}(c_i, c_j) \right|^{2}
$$

Domain, closure, identity, symmetry, sampled triangle inequality, and finite non-negative loss are verified. Deterministic synthetic tangent inputs are test fixtures, not learned embeddings or evidence that hyperbolic geometry beats Euclidean baselines.

## 4. Candidate Bitwise MoE Router

$$
e_{\mathrm{pred}}(c) = \mathrm{Extract}(c, \text{0xFF000000}, 24) \bmod E
$$

$$
P(e \mid x, c) = (1 - \alpha) \cdot \mathrm{Softmax}_{e}(\mathbf{W}_g \mathbf{h}_x) + \alpha \cdot \delta \big( e,\ e_{\mathrm{pred}}(c) \big)
$$

The reference validates routing range, modulo consistency, non-negative normalized probabilities, and $\alpha = 0$ / $\alpha = 1$ endpoints. It does not demonstrate latency, load balance, or quality gains.

## 5. Candidate HDC Representation

For $D = 10{,}000$ and field bases $\mathbf{B}_k \in \{-1, +1\}^{D}$:

$$
\Pi^{p}([v_0, v_1, \ldots, v_{D-1}]) = [v_{D-p}, \ldots, v_{D-1}, v_0, \ldots, v_{D-p-1}]
$$

$$
\mathbf{H}(c) = \mathrm{sign} \left( \sum_{k \in K} \Pi^{\mathrm{Extract}(c, M_k, S_k)}(\mathbf{B}_k) \right)
$$

$$
\mathrm{Sim}_{\mathrm{HDC}}(\mathbf{H}_1, \mathbf{H}_2) = \frac{\mathbf{H}_1 \cdot \mathbf{H}_2}{D}
$$

The reference fixes $\mathrm{sign}(0) = +1$ and derives bases from SHA-256 for reproducibility. It verifies permutation composition, output range, self-similarity, symmetry, and $[-1, 1]$ bounds, not task quality, memory, or latency benefits.

## 6. Verification and External Review

The verification artifacts for these formulas are staged with the morphology-computing experiment package (research branch, pending experiment-track merge):

- Unified formula verification report (`experiments/morphology_computing/reports/FORMAL_FORMULA_VERIFICATION_REPORT.md`)
- Machine-readable verification manifest (`experiments/morphology_computing/reports/formal_formula_verification_manifest.json`)
- P1 self-validation and external-review method (`docs/specification/P1_EXTERNAL_REVIEW_METHOD.md`, research branch)
- External review packet (`experiments/morphology_computing/review_packets/P1_EXTERNAL_INDEPENDENT_REVIEW_PACKET_EDITABLE.csv`)

Passing mathematics does not lift the scientific gate. P1 still needs external row-level source confirmation, independently reviewed negatives, and frozen candidate pools before retrieval, geometry, routing, or HDC task claims can be evaluated.
