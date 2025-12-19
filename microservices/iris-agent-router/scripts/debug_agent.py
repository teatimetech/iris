
import sys
import os
sys.path.append('/app')
from core.agents.agent_router import execute_trade_node, AgentState
from core.tools.finance_tools import get_current_price

print("--- DEBUGGING AGENT ---")
mock_state = {
    "user_id": "test-user",
    "messages": [("user", "Invest $2500 in a risk-balanced high-growth portfolio")],
    "intent": "TRADE",
    "tool_outputs": {}
}

print("Invoking execute_trade_node...")
try:
    result = execute_trade_node(mock_state)
    print("--- RESULT ---")
    print(result)
except Exception as e:
    print(f"--- ERROR ---")
    print(e)
