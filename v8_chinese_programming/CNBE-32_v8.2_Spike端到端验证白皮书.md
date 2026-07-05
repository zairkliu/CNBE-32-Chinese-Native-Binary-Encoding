# CNBE-32 v8.2 Spike 端到端验证实验白皮书

## 一、实验背景

### 1.1 v8.1 的终点

v8.1 完成了：
- 4 个测试程序全部编译通过
- 81.6KB Skill 表集成到运行时
- 编译器功能完整

但缺少 Spike 端到端运行验证 —— 仅有汇编代码，无实际执行日志。

### 1.2 v8.2 目标

| 目标 | 状态 |
|------|:----:|
| 修正 test_struct（同部首比较） | ✅ |
| 创建 test_hello 文本输出程序 | ✅ |
| 创建 Spike 一键运行脚本 | ✅ |
| 安装 RISC-V 工具链 | 🔄 环境受限 |
| Spike 端到端运行 | 🔄 依赖工具链 |

## 二、环境说明

### 2.1 当前环境限制

WSL Ubuntu 24.04 LTS 的 apt 网络连接在本次实验中不稳定，无法完成 RISC-V 工具链的安装。具体表现为：

| 操作 | 结果 | 原因 |
|------|:----:|------|
| `apt-get install gcc-riscv64-linux-gnu` | ⏱ 超时 | WSL HTTP 连接挂起 |
| `curl http://archive.ubuntu.com` | ⏱ 超时 | 出站连接被阻塞 |
| `nslookup archive.ubuntu.com` | ✅ | DNS 解析正常 |

**后续步骤**：在具备网络连接的 WSL/Ubuntu 环境中运行以下命令即可完成验证。

### 2.2 所需工具链

```bash
# 安装 RISC-V 交叉编译器
sudo apt install -y gcc-riscv64-linux-gnu binutils-riscv64-linux-gnu

# 安装 Spike 和 pk（如 apt 中无，则从源码编译）
git clone https://github.com/riscv-software-src/riscv-isa-sim.git
cd riscv-isa-sim && mkdir build && cd build
../configure --prefix=/usr/local && make -j$(nproc) && sudo make install

git clone https://github.com/riscv-software-src/riscv-pk.git
cd riscv-pk && mkdir build && cd build
../configure --prefix=/usr/local --host=riscv64-linux-gnu
make -j$(nproc) && sudo make install
```

## 三、实验准备

### 3.1 修正 test_struct（同部首比较）

将测试字符从"你/我"(不同部首)改为**森/林**(同为木部首)：

| 字 | Unicode | 部首 | 预期 |
|:--:|:-------:|:----:|:----:|
| 森 | U+68EE | 木(75) | — |
| 林 | U+6797 | 木(75) | — |
| ↑比较 | — | 部首1==部首2 | **输出 1（同部首）** |

```cnbe
子程序 struct_compare, 整数
    整数 编码1 = 取编码(26862)    # 森
    整数 编码2 = 取编码(26576)    # 林
    整数 部首1 = 取部首(编码1)
    整数 部首2 = 取部首(编码2)
    如果 (部首1 == 部首2)
        输出(1)
    否则
        输出(0)
    结束如果
返回(0)
```

**验证逻辑**：`取编码(森)` → `cnhe.map` → CNBE编码 → `取部首()` → `cnhe.extract f=0` → 部首值(75) → 比较 → 相等 → 输出 1。

### 3.2 新增 test_hello（文本输出）

```cnbe
子程序 hello_test, 整数
    输出(42)
返回(0)
```

预期输出：`42`

## 四、编译器验证

### 4.1 5 个测试程序编译结果

| 测试 | 说明 | 指令数 | 词法 | 语法 | 代码生成 |
|:----:|------|:------:|:----:|:----:|:--------:|
| test_loop | 循环求和 0+...+9=45 | 34 | ✅ | ✅ | ✅ |
| test_struct | CNBE 部首比较（森/林）| 48 | ✅ | ✅ | ✅ |
| test_cluster | CNBE 距离计算（编码比较）| 27 | ✅ | ✅ | ✅ |
| test_array | 数组求和 0+1+2+3+4=10 | 34 | ✅ | ✅ | ✅ |
| test_hello | 文本输出（输出 42）| 16 | ✅ | ✅ | ✅ |

### 4.2 一键运行脚本

`scripts/run_v82.sh` 自动执行完整流程：

```bash
# 1. 编译 5 个测试程序
python3 src/compiler.py tests/test_struct.cnbe -o output/test_struct.s
python3 src/compiler.py tests/test_loop.cnbe -o output/test_loop.s
# ... etc for all 5

# 2. 交叉编译为 ELF
riscv64-linux-gnu-gcc -march=rv64im -static output/test_struct.s \
    src/runtime/cnbe_runtime.c -o output/test_struct.elf

# 3. Spike 运行
spike pk output/test_struct.elf

# 4. 记录日志到 results/v82_spike_log.txt
```

## 五、预期 Spike 运行结果

以下是在完整环境中预期看到的输出（基于汇编代码和 Skill 表验证）：

### 5.1 test_loop（循环求和）

```
bbl loader
45
程序正常退出
```

**解释**：`计次循环(10)` 执行 0+0+1+2+...+9 = 45。循环体：`总和 = 总和 + i`。

### 5.2 test_struct（部首比较）

```
bbl loader
1
程序正常退出
```

**解释**：森(26862)和林(26576)均为木部，部首相同，输出 1。

### 5.3 test_cluster（距离计算）

```
bbl loader
128
程序正常退出
```

**解释**：取编码(27743)=江, 取编码(27827)=河, cnbe_cmp 计算加权距离。

### 5.4 test_array（数组处理）

```
bbl loader
10
程序正常退出
```

**解释**：0+1+2+3+4 = 10。简化版循环。

### 5.5 test_hello（文本输出）

```
bbl loader
42
程序正常退出
```

**解释**：直接输出整数常量 42。

## 六、与全系列的关系

```
v1-v4:  编码语义可被理解
v5:     多模型对比
v6:     数值特征优化
v7:     RISC-V 硬件验证
v8.0:   中文编程编译器
v8.1:   完整编译器 + Skill表
v8.2:   Spike端到端验证 ← 本次（环境受限，脚本就绪）
```

## 七、结论

v8.2 完成了 Spike 端到端验证的所有准备工作：5 个测试程序编译通过，test_struct 修正为正确的同部首比较（森/林），一键运行脚本就绪。

由于当前 WSL 环境网络受限无法安装 RISC-V 工具链，Spike 实际运行需在有网络连接的 Ubuntu 环境中执行 `bash scripts/run_v82.sh`。

**一旦工具链就绪，端到端验证链即可闭合：中文源码 → CNBE 编译器 → RISC-V 汇编 → ELF 链接 → Spike 执行 → 输出日志。**

## 八、快速开始（在工具链就绪的机器上）

```bash
cd CNBE-32-Chinese-Native-Binary-Encoding/v8_chinese_programming
bash scripts/run_v82.sh
```

产出文件：`results/v82_spike_log.txt`

许可证：木兰宽松许可证 v2 (Mulan PSL v2)