#!/bin/bash

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
START_SCRIPT="$SCRIPT_DIR/scripts/start_local.sh"

if [ ! -x "$START_SCRIPT" ]; then
  printf "未找到启动脚本：%s\n" "$START_SCRIPT"
  printf "\n按回车键关闭窗口..."
  read -r _
  exit 1
fi

export TRADINGAGENTS_LAUNCHED_FROM_COMMAND=1
"$START_SCRIPT"
exit $?
