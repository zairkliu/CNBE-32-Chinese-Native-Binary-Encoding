# CNBE-32 中文原生二进制编码展示程序说明

## 软件基本信息

- 软件名称：CNBE-32 中文原生二进制编码展示程序
- 建议版本：V1.0
- 运行环境：Windows 11 64 位、macOS、Linux x64
- 开发语言：Python 3、Tkinter、SQLite
- 入口命令：`cnbe32-demo`
- Windows 打包脚本：`tools/windows/build_demo_exe.ps1`
- macOS 打包脚本：`tools/macos/build_demo_app.sh`
- Linux 打包脚本：`tools/linux/build_demo_exe.sh`

## 功能范围

本程序用于展示 CNBE-32 项目的编码输出和项目规划，适合软件著作权申请、现场演示和内部评审。

主要功能包括：

1. 汉字输入与逐字编码查询；
2. Unicode、CNBE-32 十六进制、十进制和 32 位二进制输出；
3. 部首/根编号、笔画数、结构类型、字形索引、扩展位字段拆解；
4. standard / legacy / pending / missing 状态展示；
5. 项目介绍、操作流程、实施规划和软著材料页展示；
6. 演示结果复制，便于形成测试记录或申请材料截图。

## Windows 11 64 位打包

在 Windows 11 64 位电脑上安装 Python 3.10 或更高版本，然后在项目根目录打开 PowerShell：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\tools\windows\build_demo_exe.ps1
```

打包完成后，可执行程序位置：

```text
dist\CNBE32-Demo\CNBE32-Demo.exe
```

如果需要单独命名，可执行：

```powershell
.\tools\windows\build_demo_exe.ps1 -AppName "CNBE32-Copyright-Demo"
```

## macOS 打包

在 macOS 电脑上执行：

```bash
bash tools/macos/build_demo_app.sh
```

打包完成后，应用位置：

```text
dist/CNBE32-Demo.app
```

## Linux x64 打包

在 Linux x64 环境中执行：

```bash
bash tools/linux/build_demo_exe.sh
```

打包完成后，可执行程序位置：

```text
dist/CNBE32-Demo/CNBE32-Demo
```

如果系统缺少 Tkinter，请先安装对应发行版的 Tk 支持包，例如 Ubuntu：

```bash
sudo apt-get install python3-tk
```

## GitHub Release 发布包

发布 demo 时，可在三种系统分别执行上述打包脚本，然后将产物上传到同一个 GitHub Release。建议使用 `demo-v*` 形式的标签：

```bash
git tag demo-v1.0.0
git push origin demo-v1.0.0
```

建议 Release 资产包括：

- `CNBE32-Demo-Windows-x64.zip`
- `CNBE32-Demo-macOS.zip`
- `CNBE32-Demo-Linux-x64.tar.gz`

## 本地开发运行

```bash
python -m pip install -e .
cnbe32-demo
```

也可以直接运行：

```bash
python -m cnbe32_demo.app
```

## 演示步骤

1. 打开 `CNBE32-Demo.exe`。
2. 在“编码演示”页输入示例文本，例如 `中国软件著作权 CNBE-32`。
3. 点击“执行编码演示”。
4. 查看每个字符的 Unicode、CNBE-32、32 位二进制和字段拆解。
5. 切换到“项目展示”“操作流程”“实施规划”“软著材料”页，展示项目组成和开发计划。
6. 使用“复制结果”保存演示输出，配合截图形成申请材料。

## 软著申请表达建议

建议将本软件表述为“中文结构编码研究与展示软件”或“CNBE-32 编码展示程序”。项目当前以国家语言文字规范为对齐目标，不应在申请材料中写成“已获得国家标准认证”。

建议随附材料：

- exe 展示程序；
- 本说明文档；
- 软件功能说明；
- 操作截图；
- 测试记录；
- 项目 README、治理文档和报告摘要；
- 源代码前后连续页。
