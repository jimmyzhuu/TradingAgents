# TradingAgents: A-Share Enhanced Fork

> An independently maintained fork of TradingAgents focused on China A-share research, market-aware agent workflows, and structured multi-agent decision making.
>
> 一个独立维护的 TradingAgents 增强版 fork，重点面向中国 A 股研究、市场感知型智能体工作流，以及结构化多智能体决策。

## Overview / 项目简介

TradingAgents is a multi-agent trading research framework built on LangGraph. This fork keeps the original agent topology, then extends it with a market-profile layer, structured decision outputs, persistent decision memory, benchmark-aware reflection, and a practical A-share compatibility workflow.

TradingAgents 是一个基于 LangGraph 的多智能体交易研究框架。本 fork 保留了原始的智能体拓扑结构，并在此基础上扩展了市场配置层、结构化决策输出、持久化决策记忆、基准感知反思，以及更贴近中国 A 股研究场景的兼容工作流。

This repository is best understood as a research and simulation system rather than a production brokerage execution platform.

这个仓库更适合被理解为研究与模拟系统，而不是生产级券商交易执行平台。

## Why This Fork Exists / 为什么会有这个 Fork

The upstream project is a strong general multi-agent trading framework, but many defaults are US-centric. This fork exists to make the workflow more usable for mainland China equity research without rewriting the whole graph from scratch.

上游项目本身是一个很强的通用多智能体交易框架，但很多默认设定更偏向美股语境。这个 fork 的目标，是在不推翻原有图结构的前提下，把它改造成更适合中国大陆股票研究的版本。

## Key Characteristics / 主要特点

- Structured decision chain for the Research Manager, Trader, and Portfolio Manager.
  研究经理、交易员、组合经理都支持结构化决策输出，不再只依赖松散自然语言。
- Persistent decision log with deferred reflection.
  决策日志会持久化保存，并在收益兑现后补写反思结果。
- Benchmark-aware reflection instead of hardcoded `SPY`.
  反思链路不再写死 `SPY`，而是按当前市场配置使用对应基准。
- Market-profile layer for ticker normalization, calendars, benchmark defaults, and output language.
  增加了市场配置层，统一处理 ticker 规范化、交易日历、默认基准和默认输出语言。
- China A-share research workflow built into the existing graph.
  在原有 graph 中直接接入了中国 A 股研究工作流，而不是另起一套分支架构。
- Checkpoint resume for long-running analyses.
  对长时间分析流程支持 checkpoint 续跑。

## A-Share Enhancements / A 股增强内容

### Supported Today / 当前已支持

- Mainland ticker normalization for `SH`, `SZ`, and `BJ`.
  支持 `SH`、`SZ`、`BJ` 的大陆股票代码规范化。
- A-share OHLCV routing and indicator support.
  支持 A 股行情与技术指标数据路由。
- A-share fundamentals, company news, and exchange-filed announcements.
  支持 A 股基础财务、公司新闻和交易所公告数据。
- Announcement-aware research prompts.
  研究提示词已经具备“公告优先”的 A 股语境。
- A-share rule-aware Trader and Portfolio Manager outputs.
  交易员和组合经理的输出会显式考虑 A 股规则约束。
- Chinese output as the default for `cn_a`.
  `cn_a` 市场默认中文输出。

### A-Share-Specific Behavior / A 股专属行为

- The CLI asks for market selection before ticker input.
  CLI 会先要求选择市场，再输入 ticker。
- Mainland ticker examples are shown in the CLI.
  CLI 会展示 A 股 ticker 示例。
- Reflection uses the configured mainland benchmark such as `000300.SH`.
  反思阶段会使用配置好的大陆基准，例如 `000300.SH`。
- Research prompts prioritize exchange-filed announcements and Chinese-language news flow.
  研究提示词会优先关注交易所公告和中文新闻流。
- Structured outputs can surface T+1, price-limit, suspension, liquidity, and disclosure constraints.
  结构化输出可以显式呈现 T+1、涨跌停、停牌、流动性和信息披露约束。

## Current Boundaries / 当前边界

- This is still a research-first system, not a live brokerage integration.
  这仍然是一个以研究为中心的系统，不是实盘券商接入系统。
- A-share market rules are surfaced in prompts and structured outputs, not enforced by a full exchange simulator.
  A 股市场规则目前主要体现在提示词和结构化输出中，而不是由完整交易所模拟器硬性执行。
- Hong Kong support is not yet at the same maturity level as A-share support.
  港股支持目前还没有达到与 A 股同等的完成度。
- A-share fundamentals and announcement semantics can still be improved further.
  A 股财务口径和公告语义层后续仍有继续增强空间。

## Quick Start / 快速开始

### 1. Clone / 克隆仓库

```bash
git clone https://github.com/jimmyzhuu/TradingAgents.git
cd TradingAgents
```

### 2. Create an environment / 创建环境

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

### 3. Configure API keys / 配置 API Key

TradingAgents supports multiple LLM providers. At minimum, configure the provider you plan to use.

TradingAgents 支持多个大模型提供方。最少只需要配置你准备使用的那个提供方。

```bash
export OPENAI_API_KEY=...
export GOOGLE_API_KEY=...
export ANTHROPIC_API_KEY=...
export XAI_API_KEY=...
export DEEPSEEK_API_KEY=...
export DASHSCOPE_API_KEY=...
export ZHIPU_API_KEY=...
export OPENROUTER_API_KEY=...
export ALPHA_VANTAGE_API_KEY=...
```

## CLI Usage / CLI 用法

Launch the interactive CLI:

启动交互式 CLI：

```bash
tradingagents
# or
python -m cli.main
```

For A-share runs, the CLI will guide you through:

对于 A 股分析，CLI 会引导你完成以下步骤：

1. Select market first.
   先选择市场。
2. Enter a mainland ticker such as `600519.SH` or `000001.SZ`.
   输入大陆股票代码，例如 `600519.SH` 或 `000001.SZ`。
3. Choose an analysis date.
   选择分析日期。
4. Keep Chinese as the default output language for `cn_a`.
   对于 `cn_a`，默认保留中文输出。

## Minimal A-Share Example / 最小 A 股示例

```python
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

config = DEFAULT_CONFIG.copy()
config.update(
    {
        "market": "cn_a",
        "benchmark_symbol": "000300.SH",
        "calendar_code": "XSHG",
        "output_language": "Chinese",
        "data_vendors": {
            "core_stock_apis": "a_share",
            "technical_indicators": "a_share",
            "fundamental_data": "a_share",
            "news_data": "a_share",
        },
    }
)

ta = TradingAgentsGraph(debug=True, config=config)
_, decision = ta.propagate("600519.SH", "2026-03-28")
print(decision)
```

## Architecture Notes / 架构说明

This fork keeps the original multi-agent flow:

这个 fork 保留了原始的多智能体链路：

- Analyst team
  分析师团队
- Research debate
  研究辩论
- Trader proposal
  交易员建议
- Risk debate
  风险辩论
- Portfolio Manager decision
  组合经理最终决策

What changed is the wiring around that graph:

发生变化的主要是图外层和节点工具能力：

- market-aware configuration
  市场感知配置
- A-share data routing
  A 股数据路由
- structured outputs
  结构化输出
- benchmark-aware reflection
  基准感知反思
- persistent decision memory
  持久化决策记忆
- checkpoint resume
  checkpoint 续跑

## Persistence And Recovery / 持久化与恢复

### Decision Log / 决策日志

Each completed run appends a decision to `~/.tradingagents/memory/trading_memory.md`. On later runs, the system can resolve realized returns, compute alpha versus the configured benchmark, generate a concise reflection, and reinject those lessons into future analysis.

每次完成分析后，系统都会把决策写入 `~/.tradingagents/memory/trading_memory.md`。之后的运行中，系统可以补算真实收益、计算相对配置基准的 alpha、生成简短反思，并把这些经验重新注入后续分析。

### Checkpoint Resume / Checkpoint 续跑

Checkpoint resume is opt-in. When enabled, LangGraph can resume from the last successful node after an interruption instead of restarting from zero.

Checkpoint 续跑是可选功能。启用后，如果分析流程中断，LangGraph 可以从最近一个成功节点继续，而不是从头重跑。

## Repository Positioning / 仓库定位

This repository is not presented as the upstream official project. It is an independently maintained enhanced fork with a narrower and more practical focus on A-share research workflows.

这个仓库不是以上游官方项目的身份呈现，而是一个独立维护的增强版 fork，目标更聚焦，也更偏向 A 股研究工作流的实用落地。

## Upstream Acknowledgements / 上游致谢

This repository started as a fork of [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents).

这个仓库起步于 [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) 的 fork。

We appreciate the original authors for open-sourcing the core framework and making the original multi-agent design available to the community.

感谢原作者开源核心框架，并把原始的多智能体设计贡献给社区。

This fork is now maintained independently. Any A-share enhancements, market-profile changes, structured workflow additions, and README positioning in this repository should be understood as fork-specific work rather than upstream project statements.

这个 fork 现在是独立维护的。当前仓库中的 A 股增强、市场配置调整、结构化工作流扩展，以及 README 的项目定位，都应理解为本 fork 自身的工作，而不是上游项目的官方表述。

## License / 许可证

This repository remains distributed under the Apache License 2.0. See [LICENSE](LICENSE).

本仓库继续采用 Apache License 2.0 进行分发。详见 [LICENSE](LICENSE)。
