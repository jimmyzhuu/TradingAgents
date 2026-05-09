# One-Click Launch Design

## Summary

Add a stable macOS one-click launcher for the local `TradingAgents` CLI workflow. The launcher should let the user start the existing interactive CLI by double-clicking a file in Finder, while keeping the real startup logic in a reusable shell script under `scripts/`.

## Context

The repository already supports local startup through the Python virtual environment and an interactive CLI entry point. The current startup path works for terminal-first usage, but it is not convenient for a user who wants to launch the app with one click.

The project root visible to the user is:

- `/Users/zimingzhu/githubProject/TradingAgent/TradingAgents`

The effective local runtime path is:

- local virtual environment in `.venv`
- environment variables from `.env`
- interactive CLI entry point through `python -m cli.main analyze`

## Goals

- Provide a double-clickable launcher for macOS.
- Default to the existing local `.venv` runtime path.
- Keep the terminal window open after exit so the user can continue interacting or read errors.
- Show direct Chinese error messages for the most common setup problems.
- Separate Finder-facing launcher behavior from reusable startup logic.

## Non-Goals

- No GUI application for this iteration.
- No Docker-first startup path for this iteration.
- No automatic environment bootstrap such as creating `.venv` or installing dependencies.
- No change to the existing CLI interaction model.

## Chosen Approach

Use two files:

- `start_tradingagents.command`
- `scripts/start_local.sh`

`start_tradingagents.command` is the thin macOS entry file meant for Finder double-click. It should resolve its own directory, switch into the repository root, and invoke the formal startup script.

`scripts/start_local.sh` contains the actual startup workflow. It should validate the runtime prerequisites and then launch the existing CLI with:

```bash
.venv/bin/python -m cli.main analyze
```

This command is preferred over calling the console script directly because it makes the Python entry point explicit and avoids ambiguity around PATH or wrapper behavior.

## File Responsibilities

### `start_tradingagents.command`

Responsibilities:

- act as the user-facing double-click entry
- switch to the repository root reliably
- call `scripts/start_local.sh`
- keep the terminal session usable after the launched process exits

Design constraints:

- keep logic minimal
- avoid duplicating environment checks already handled by `scripts/start_local.sh`

### `scripts/start_local.sh`

Responsibilities:

- verify the repository root can be resolved
- verify `.venv/bin/python` exists
- verify `.env` exists
- launch the interactive CLI with the local virtual environment
- return a clear exit status
- pause before closing when startup cannot proceed

## Runtime Behavior

Successful path:

1. User double-clicks `start_tradingagents.command`.
2. Terminal opens and switches into the project root.
3. The launcher invokes `scripts/start_local.sh`.
4. The startup script validates required local files.
5. The script runs `.venv/bin/python -m cli.main analyze`.
6. The CLI remains interactive in the same terminal window.
7. When the CLI exits, the window remains available so the user can inspect output.

Failure path:

- If the project root cannot be determined, print a direct Chinese message and stop.
- If `.venv/bin/python` is missing, tell the user to create the virtual environment first.
- If `.env` is missing, tell the user to create or restore `.env` first.
- If the Python command exits with an error, print that startup failed and preserve the terminal output for troubleshooting.

## Error Message Style

Error messages should be:

- in plain Chinese
- short and actionable
- specific about what file or prerequisite is missing

Examples of tone:

- `未找到 .venv，请先创建本地虚拟环境。`
- `未找到 .env，请先补充环境变量配置。`
- `启动失败，请查看上面的报错信息。`

## Extensibility

The design should keep future enhancements centered in `scripts/start_local.sh`, so the double-click entry file stays stable.

Likely future extensions:

- add optional Docker startup
- add checkpoint flags
- add simple log capture
- add argument passthrough or mode selection

## Testing Strategy

For this iteration, verification should focus on behavior that matters most:

- confirm both files exist in the expected locations
- confirm both files are executable
- confirm the launcher resolves into the repository root correctly
- confirm missing prerequisite cases produce readable messages
- confirm the success path reaches the interactive CLI command

Because the main output is shell behavior, lightweight manual verification is acceptable here. If needed later, shell checks can be added for path resolution and error branches.

## Risks And Trade-Offs

- A `.command` launcher is macOS-specific, but that matches the user's requested one-click workflow.
- The solution still opens Terminal rather than a standalone app window, but this is the most reliable match for an interactive CLI.
- The launcher assumes the repository layout remains stable. Keeping path logic centralized reduces maintenance cost if the layout changes later.

## Implementation Outline

1. Add `scripts/start_local.sh` with prerequisite checks and the canonical local startup command.
2. Add `start_tradingagents.command` as the Finder-facing double-click entry.
3. Mark both files executable.
4. Run manual verification for prerequisite failure paths and the normal startup path.
