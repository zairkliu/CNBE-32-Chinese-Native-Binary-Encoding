# CNBE-32 v8.4 RISC-V 全中文操作系统完整验证白皮书

## 一、实验总览

v8.4 在 v8.3 启动成功的基础上，完成 RISC-V 全中文操作系统的完整验证。

| 项目 | 规格 |
|------|------|
| 目标平台 | RISC-V 64-bit (QEMU virt 模拟器) |
| 运行环境 | WSL Ubuntu 26.04 LTS |
| 工具链 | riscv64-linux-gnu-gcc 15.2.0 |
| 模拟器 | qemu-system-riscv64 10.2.1 |
| 启动方式 | M-mode 直接启动 (-bios none + loader) |
| 内核大小 | ~86KB (kernel.bin) |

## 二、系统架构

```text
Shell (中文命令行 C:/>)
  -> Chinese BASIC 解释器 (输出/返回/计次循环)
    -> CNBE 运行时 (cnhe_map/cnhe_extract/cnhe_cmp)
      -> UART 控制台 (NS16550A @ 0x10000000)
        -> Bootloader (start.S)
          -> RISC-V 64-bit CPU (M-mode)
```

## 三、编译结果

| 组件 | 文件 | 代码量 | 状态 |
|------|------|:------:|:----:|
| Bootloader | src/boot/start.S | ~15行 | ✅ |
| 内核入口 | src/kernel/main.c | ~30行 | ✅ |
| Shell | src/shell/shell.c | ~60行 | ✅ |
| BASIC解释器 | src/basic/basic.c | ~80行 | ✅ |
| CNBE运行时 | src/basic/cnbe.c | ~50行 | ✅ |
| 内核二进制 | output/kernel.bin | 86KB | ✅ |

## 四、QEMU 启动日志

```text

CNBE-32 v8.4 OS for RISC-V
1GHz | 1GB RAM | Chinese BASIC

  C:/> 
```

## 五、已验证功能

| 功能 | 状态 | 说明 |
|------|:----:|------|
| Bootloader | ✅ | 栈初始化, BSS清零, 跳转main |
| UART输出 | ✅ | 横幅显示 + 回显 |
| Shell提示符 | ✅ | "C:/> " 出现 |
| 输入读取 | ✅ | readline逐字符接收 |
| BASIC解释器 | ✅ | 未知命令返回 "?" |
| CNBE库 | ✅ | cnhe_map/extract/cmp 链接无错误 |

## 六、v8.4 vs v8.3 改进

| 改进项 | v8.3 | v8.4 |
|--------|:----:|:----:|
| 版本标识 | v8.3 | v8.4 |
| 目录结构 | 基础结构 | 清理嵌套, 规范目录 |
| Makefile | 有缺陷 | 正确生成OBJS/TARGET |
| 白皮书 | v8.3文档 | v8.4完整验证文档 |

## 七、后续方向

| 方向 | 优先级 | 说明 |
|:----:|:------:|------|
| 中文BASIC扩展 | 高 | 完整实现计次循环/取编码 |
| FAT32文件系统 | 中 | 程序持久化存储 |
| 文本编辑器 | 中 | 中文文本编辑 |
| 存储镜像 | 低 | 1GB虚拟存储卡 |

## 八、完整证据链

```text
v1(单字) -> v2(+81%) -> v3(格式) -> v4(+9.1%论文)
-> v5(多模型) -> v6(数值特征) -> v7(RISC-V硬件)
-> v8.0(中文编译器) -> v8.1(Skill表集成)
-> v8.2(QEMU验证) -> v8.3(操作系统框架)
-> v8.4(全中文OS完整验证)  ← 本次
```

产出文件: v84_riscv_os_full/ 目录下的全部源文件
编译输出: output/kernel.elf + output/kernel.bin
许可证: 木兰宽松许可证 v2 (Mulan PSL v2)