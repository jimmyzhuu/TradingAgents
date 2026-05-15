from pathlib import Path
import os

import pytest


ROOT = Path(__file__).resolve().parent.parent
START_COMMAND = ROOT / "start_tradingagents.command"
START_LOCAL = ROOT / "scripts" / "start_local.sh"


@pytest.mark.unit
def test_start_local_script_contains_local_cli_flow():
    assert START_LOCAL.exists()

    content = START_LOCAL.read_text()

    assert "#!/bin/bash" in content
    assert ".venv/bin/python" in content
    assert ".env" in content
    assert "-m cli.main" in content
    assert "-m cli.main analyze" not in content
    assert "未找到 .venv" in content
    assert "未找到 .env" in content


@pytest.mark.unit
def test_command_launcher_points_to_formal_start_script():
    assert START_COMMAND.exists()

    content = START_COMMAND.read_text()

    assert "#!/bin/bash" in content
    assert "scripts/start_local.sh" in content
    assert "TRADINGAGENTS_LAUNCHED_FROM_COMMAND" in content


@pytest.mark.unit
def test_launcher_files_are_executable():
    assert os.access(START_COMMAND, os.X_OK)
    assert os.access(START_LOCAL, os.X_OK)
