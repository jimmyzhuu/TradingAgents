#!/bin/bash

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
ENV_FILE="$ROOT_DIR/.env"

pause_if_needed() {
  if [ "${TRADINGAGENTS_LAUNCHED_FROM_COMMAND:-0}" = "1" ]; then
    printf "\n按回车键关闭窗口..."
    read -r _
  fi
}

fail() {
  printf "%s\n" "$1"
  pause_if_needed
  exit 1
}

cd "$ROOT_DIR" || fail "未找到项目目录，无法启动。"

if [ ! -x "$PYTHON_BIN" ]; then
  fail "未找到 .venv，请先创建本地虚拟环境。"
fi

if [ ! -f "$ENV_FILE" ]; then
  fail "未找到 .env，请先补充环境变量配置。"
fi

"$PYTHON_BIN" -m cli.main "$@"
STATUS=$?

if [ "$STATUS" -ne 0 ]; then
  printf "启动失败，请查看上面的报错信息。\n"
fi

pause_if_needed
exit "$STATUS"
