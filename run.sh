#!/bin/bash
# 启动脚本 - 直接运行源码
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "错误: 需要安装 uv (https://docs.astral.sh/uv/)"
    exit 1
fi

# 安装依赖并运行
uv sync --frozen
uv run python main.py "$@"
