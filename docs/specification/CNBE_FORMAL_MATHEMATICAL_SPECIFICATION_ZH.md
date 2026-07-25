# CNBE-32 形态计算形式化数学说明

**定位：** 研究性数学规范，不是国家语言文字标准，也不是运行时字段正确性的来源。
**验证状态：** 13 个公式已完成参考实现的数学或数值性质验证；任务效果仍待独立外部审阅。
**英文对应：** [CNBE-32 Formal Mathematical Specification](CNBE_FORMAL_MATHEMATICAL_SPECIFICATION.md)
**配套展示文档：** [CNBE-32 Mathematical Structure](../CNBE32_MATHEMATICAL_STRUCTURE.md)

## 1. 位域与二进制向量

令一个 CNBE 字为无符号 32 位整数：

$$
c \in \{0, 1, \ldots, 2^{32}-1\}.
$$

第 $k$ 个字段以掩码 $M_k$、位移 $S_k$ 提取：

$$
\mathrm{Extract}(c, M_k, S_k) = (c \land M_k) \gg S_k
$$

对应的低位优先二进制向量为：

$$
\Phi(c) = [b_0, b_1, \ldots, b_{31}]^{\mathsf{T}}, \qquad b_i = \left\lfloor \frac{c}{2^i} \right\rfloor \bmod 2
$$

其逆变换为：

$$
c = \sum_{i=0}^{31} \Phi(c)_i \cdot 2^i
$$

上述表示层已在 6,568 条冻结 P0 记录与 11 个 golden vectors 上验证可逆；它不表示相邻 bit 或字段数值本身具有语言学距离含义。

## 2. 加权形态汉明距离

对字符对 $c_1, c_2$，形式化规范中的五字段距离为：

$$
\mathcal{D}_{\mathrm{morph}}(c_1, c_2) = \sum_{k \in K} w_k \cdot \frac{\mathrm{POPCNT}\Big( (c_1 \land M_k) \oplus (c_2 \land M_k) \Big)}{d_k}
$$

这里 $d_k$ 是字段位宽，$\oplus$ 是按位异或，$\mathrm{POPCNT}$ 是置位数。原始研究权重为：

$$
(w_{\mathrm{radix}},\ w_{\mathrm{stroke}},\ w_{\mathrm{struct}},\ w_{\mathrm{index}},\ w_{\mathrm{ext}}) = (0.4,\ 0.2,\ 0.2,\ 0.1,\ 0.1)
$$

参考实现已验证恒等性、对称性、$[0, 1]$ 有界性和字段隔离增量；这些权重尚未获得独立语言学任务的有效性证明，尤其不能把 `index` 与 `ext` 直接解释成形态证据。

## 3. 庞加莱双曲空间候选模型

定义 $d$ 维庞加莱球：

$$
\mathbb{B}^{d} = \{ \mathbf{x} \in \mathbb{R}^{d} : \| \mathbf{x} \| < 1 \}
$$

### 3.1 测地线距离

$$
d_{\mathbb{B}}(\mathbf{u}, \mathbf{v}) = \mathrm{arcosh} \left( 1 + 2 \, \frac{\| \mathbf{u} - \mathbf{v} \|^{2}}{(1 - \| \mathbf{u} \|^{2})(1 - \| \mathbf{v} \|^{2})} \right)
$$

### 3.2 莫比乌斯加法

$$
\mathbf{u} \oplus_{\mathbb{B}} \mathbf{v} = \frac{(1 + 2 \langle \mathbf{u}, \mathbf{v} \rangle + \| \mathbf{v} \|^{2}) \, \mathbf{u} + (1 - \| \mathbf{u} \|^{2}) \, \mathbf{v}}{1 + 2 \langle \mathbf{u}, \mathbf{v} \rangle + \| \mathbf{u} \|^{2} \| \mathbf{v} \|^{2}}
$$

### 3.3 原点指数映射

$$
\exp_{\mathbf{0}}(\mathbf{v}) = \tanh(\| \mathbf{v} \|) \, \frac{\mathbf{v}}{\| \mathbf{v} \|}
$$

当 $\mathbf{v} = \mathbf{0}$ 时，参考实现按连续延拓返回 $\mathbf{0}$。

### 3.4 单字组合表示

$$
\mathbf{z}_c = \mathbf{e}_{\mathrm{radix}} \oplus_{\mathbb{B}} \mathbf{e}_{\mathrm{struct}} \oplus_{\mathbb{B}} \mathbf{e}_{\mathrm{stroke}}
$$

### 3.5 几何对齐损失

$$
\mathcal{L}_{\mathrm{hyperbolic}} = \frac{1}{N^{2}} \sum_{i=1}^{N} \sum_{j=1}^{N} \left| d_{\mathbb{B}}(\mathbf{z}_{c_i}, \mathbf{z}_{c_j}) - \gamma \cdot \mathcal{D}_{\mathrm{morph}}(c_i, c_j) \right|^{2}
$$

已完成定义域、球内闭包、恒等性、对称性、抽样三角不等式与有限非负损失验证。当前使用的是确定性合成切空间输入，因此不构成训练嵌入或双曲模型优于欧氏模型的结论。

## 4. Bitwise MoE 候选路由

给定专家数 $E$，部首字段的确定性预路由为：

$$
e_{\mathrm{pred}}(c) = \mathrm{Extract}(c, \text{0xFF000000}, 24) \bmod E
$$

令 $\mathbf{h}_x$ 为输入表示，混合门控分布为：

$$
P(e \mid x, c) = (1 - \alpha) \cdot \mathrm{Softmax}_{e}(\mathbf{W}_g \mathbf{h}_x) + \alpha \cdot \delta \big( e,\ e_{\mathrm{pred}}(c) \big)
$$

已验证路由范围、取模一致性、概率非负性、归一化和 $\alpha = 0$ / $\alpha = 1$ 端点。尚未证明它降低端到端延迟、保持专家负载均衡或优于学习门控。

## 5. HDC 候选表征

设置超向量维数 $D = 10{,}000$，字段基向量 $\mathbf{B}_k \in \{-1, +1\}^{D}$。

### 5.1 循环位置置换

$$
\Pi^{p}([v_0, v_1, \ldots, v_{D-1}]) = [v_{D-p}, \ldots, v_{D-1}, v_0, \ldots, v_{D-p-1}]
$$

### 5.2 字段叠加编码

$$
\mathbf{H}(c) = \mathrm{sign} \left( \sum_{k \in K} \Pi^{\mathrm{Extract}(c, M_k, S_k)}(\mathbf{B}_k) \right)
$$

参考实现固定 $\mathrm{sign}(0) = +1$，并以 SHA-256 派生基向量来保证复现，而非表示训练得到的参数。

### 5.3 相似度

$$
\mathrm{Sim}_{\mathrm{HDC}}(\mathbf{H}_1, \mathbf{H}_2) = \frac{\mathbf{H}_1 \cdot \mathbf{H}_2}{D}
$$

已验证置换复合、输出取值范围、自相似性、对称性与 $[-1, 1]$ 范围。尚未证明质量、内存或延迟优势。

## 6. 验证与外部复核入口

- [统一公式验证报告](../../experiments/morphology_computing/reports/FORMAL_FORMULA_VERIFICATION_REPORT.md)
- [机器可读验证清单](../../experiments/morphology_computing/reports/formal_formula_verification_manifest.json)
- [自验证与外部独立审阅方法](P1_EXTERNAL_REVIEW_METHOD_ZH.md)（[English](P1_EXTERNAL_REVIEW_METHOD.md)）
- [外部独立审阅包](../../experiments/morphology_computing/review_packets/P1_EXTERNAL_INDEPENDENT_REVIEW_PACKET_EDITABLE.csv)

其余实验产物（关系账本、自验证包构建脚本与测试）随形态计算实验包存放，待实验轨合并时一并入库。

数学层通过不解除科学验证门槛。P1 仍需要外部人员逐行来源确认、独立审核的负例和固定候选池，之后才可评价检索、几何、路由或 HDC 的任务表现。
