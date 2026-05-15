from dotenv import load_dotenv
from tradingagents.default_config import build_cn_a_runtime_config
from tradingagents.graph.trading_graph import TradingAgentsGraph

load_dotenv()

config = build_cn_a_runtime_config()
ta = TradingAgentsGraph(debug=True, config=config)

_, decision = ta.propagate("600519.SH", "2024-05-10")
print(decision)
