import os
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_community.llms import Ollama

# Helper function imports (must be implemented in finance_tools.py)
from core.tools.finance_tools import get_market_data, lookup_rag_context, execute_trade_action, get_portfolio_details, get_activity_log, get_past_conversations

# Ollama LLM setup using the K8s service DNS name
OLLAMA_SERVICE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama-service:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
LLM = Ollama(model=OLLAMA_MODEL, base_url=OLLAMA_SERVICE_URL)

# 1. Define the Graph State
class AgentState(TypedDict):
    user_id: str
    messages: Annotated[list[tuple], add_messages] 
    intent: str 
    tool_outputs: dict # Store results from tool calls
    next_step: str # Determining next action


# 2. Define the Nodes (Functions)
def classify_intent(state: AgentState):
    """Classifies user intent (ADVICE, TRADE, PROFILE_UPDATE, etc.)."""
    last_msg_obj = state['messages'][-1]
    last_msg_text = last_msg_obj.content if hasattr(last_msg_obj, 'content') else last_msg_obj[1]
    
    last_msg = last_msg_text.lower()
    
    intent = "GENERAL_CHAT"
    if 'buy' in last_msg or 'sell' in last_msg:
        intent = 'TRADE'
    elif 'price' in last_msg or 'analyze' in last_msg or 'market' in last_msg or 'outlook' in last_msg:
        intent = 'ADVICE'
    elif 'risk' in last_msg or 'goal' in last_msg or 'portfolio' in last_msg or 'holdings' in last_msg:
        intent = 'ADVICE' # Portfolio queries also need context fetching
        
    return {"intent": intent}

def fetch_financial_data(state: AgentState):
    """Fetches real-time market data and RAG context."""
    user_id = state.get("user_id", "test-user")
    last_msg_obj = state['messages'][-1]
    text = last_msg_obj.content if hasattr(last_msg_obj, 'content') else last_msg_obj[1]
    
    # 1. Extract potential Ticker
    # MVP: Extract ticker naively (first word that looks like a ticker) or default to "SPY"
    ticker = "SPY" 
    
    words = text.split()
    for w in words:
        w_clean = w.strip(".,?!")
        if w_clean.isupper() and len(w_clean) <= 5 and w_clean.isalpha() and w_clean not in ["BUY", "SELL", "WHAT", "HOW", "WHY", "IS", "THE"]:
            ticker = w_clean
            break

    # 2. Fetch All Context
    # Parallelize in production
    market_data = get_market_data(ticker)
    rag_context = lookup_rag_context(text)
    portfolio_context = get_portfolio_details(user_id)
    activity_log = get_activity_log(user_id)
    chat_history = get_past_conversations(user_id)
    
    # 3. Aggregate
    full_context = f"""
    [User Context]
    Portfolio: {portfolio_context}
    Recent Transactions: {activity_log}
    
    [Market Intelligence]
    {market_data}
    
    [Knowledge Base]
    {rag_context}
    
    [Memory]
    {chat_history}
    """
    
    return {"tool_outputs": {"context_data": full_context}}

def execute_trade_node(state: AgentState):
    """Parses intent and executes trade."""
    last_msg_obj = state['messages'][-1]
    text = last_msg_obj.content if hasattr(last_msg_obj, 'content') else last_msg_obj[1]
    text = text.upper()
    
    # Naive extraction for MVP
    action = "BUY" if "BUY" in text else "SELL"
    
    ticker = "NVDA" # Default
    words = text.split()
    for w in words:
        w_clean = w.strip(".,?!")
        if w_clean not in ["BUY", "SELL", "SHARES", "OF"] and w_clean.isalpha():
            ticker = w_clean
            break
            
    quantity = 10.0 # Default
    for w in words:
        if w.isdigit():
            quantity = float(w)
            break
            
    # Mock price for execution based on market data (or hardcoded for safety in testing)
    price = 450.00 
    
    result = execute_trade_action(state.get("user_id", "test-user"), ticker, action, quantity, price)
    return {"tool_outputs": {"trade_result": result}}

def generate_response(state: AgentState):
    """Generates the final response based on tool outputs."""
    tool_data = state.get("tool_outputs", {})
    
    system_prompt = "You are IRIS, an intelligent financial AI agent. You have access to the user's portfolio and market data."
    
    if "context_data" in tool_data:
        system_prompt += f"\n\nUse the following context to answer the user request:\n{tool_data['context_data']}"
    if "trade_result" in tool_data:
        system_prompt += f"\n\nTrade Execution Result: {tool_data['trade_result']}"
        
    # Pass context to LLM
    formatted_msgs = [f"system: {system_prompt}"]
    
    # Only append the *last* user message because history is already in the context block
    # Or append conversation history? 
    # Since we inject "chat_history" in context, we might duplicate if we simply append all messages.
    # However, LangGraph passes state['messages']. 
    # Let's rely on LangGraph's message history but PREPEND the system prompt with context.
    
    # Actually, simpler: just format the prompt for Ollama invoke
    for msg in state['messages']:
        if hasattr(msg, 'content'):
            role = msg.type
            content = msg.content
        else:
            role, content = msg
        formatted_msgs.append(f"{role}: {content}")
        
    full_prompt = "\n".join(formatted_msgs)
    
    # Debug print
    print(f"--- PROMPT SENT TO LLM ---\n{full_prompt[:500]}...\n--------------------------")
    
    response_text = LLM.invoke(full_prompt)
    
    return {"messages": [("ai", response_text)]}

# 3. Build the LangGraph
builder = StateGraph(AgentState)
builder.add_node("classify", classify_intent)
builder.add_node("fetch_data", fetch_financial_data)
builder.add_node("execute_trade", execute_trade_node)
builder.add_node("respond", generate_response)

builder.set_entry_point("classify")

def router(state):
    intent = state['intent']
    if intent == 'TRADE':
        return "execute_trade"
    elif intent == 'ADVICE':
        return "fetch_data"
    else:
        # For general chat, we STILL might want context (memory), so let's default to fetch_data
        # unless it's a very simple greeting? 
        # Let's make "respond" capable of handling no context, but better to always fetch context for "awareness".
        return "fetch_data" 

builder.add_conditional_edges(
    "classify",
    router,
    {
        "execute_trade": "execute_trade",
        "fetch_data": "fetch_data",
        "respond": "respond"
    }
)

builder.add_edge("fetch_data", "respond")
builder.add_edge("execute_trade", "respond")
builder.add_edge("respond", END)

iris_agent = builder.compile()
