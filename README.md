### clipboard-tool
This is vibe code project.Only for test.
Use github action to build and deploy.

### How to run

```bash
uv run main.py
```

## 打包构建

### 本地打包

使用通用 spec 文件，自动适配当前平台：

```bash
# 安装依赖
uv sync

# 打包（生成 dist/clipboard-tool/ 目录）
uv run pyinstaller clipboard-tool.spec
```

### 跨平台支持

`clipboard-tool.spec` 已配置多平台自动适配：

| 平台 | `sys.platform` | pynput 后端 |
|------|---------------|------------|
| macOS (Intel & Apple Silicon) | `darwin` | `_darwin` |
| Windows | `win32` | `_win32` |
| Ubuntu / Linux | `linux` | `_xorg` |

## macOS 安装

### 方法一：.app bundle + .dmg（推荐 GUI 用户）

构建可拖拽安装的 .dmg 文件：

```bash
# 确保已安装 create-dmg
brew install create-dmg

# 构建 .dmg
./scripts/build_dmg.sh
```

输出：`dist/Clipboard Tool-0.0.1.dmg`

安装步骤：
1. 双击打开 .dmg 文件
2. 将 "Clipboard Tool" 拖拽到 Applications 文件夹
3. 从 Launchpad 或 Applications 启动

### 方法二：命令行安装（推荐开发者）

无需 sudo，安装到 `~/.local/`：

```bash
# 安装
./scripts/install.sh

# 运行
clipboard-tool
```

如果 `~/.local/bin` 不在 PATH 中，请添加到 shell 配置文件：

```bash
# ~/.zshrc 或 ~/.bashrc
export PATH="${HOME}/.local/bin:${PATH}"
```

卸载：

```bash
rm -rf ~/.local/lib/clipboard-tool
rm ~/.local/bin/clipboard-tool
```

## macOS 权限说明

首次运行需要授予**辅助功能权限**：
1. 打开 `系统设置 > 隐私与安全性 > 辅助功能`
2. 添加并勾选终端应用（Terminal / iTerm2 / VS Code）
3. 重新运行程序

## GitHub Actions 自动构建

已配置 `.github/workflows/build.yml`，自动构建并上传产物：

- **Linux**: `clipboard-tool-linux`
- **Windows**: `clipboard-tool-windows`
- **macOS**: `clipboard-tool-macos`（Universal Binary，支持 Intel & Apple Silicon）
