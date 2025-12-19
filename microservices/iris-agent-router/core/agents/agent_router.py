import os
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_ollama import OllamaLLM

# Helper function imports (must be implemented in finance_tools.py)
from core.tools.finance_tools import get_market_data, lookup_rag_context, execute_trade_action, get_portfolio_details, get_activity_log, get_past_conversations, get_current_price, build_user_context

# Ollama LLM setup using the K8s service DNS name
OLLAMA_SERVICE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
LLM = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_SERVICE_URL)

# 1. Define the Graph State
# 1. Define the Graph State
class AgentState(TypedDict):
    user_id: str
    messages: Annotated[list[tuple], add_messages] 
    intent: str 
    tool_outputs: dict # Store results from tool calls
    next_step: str # Determining next action
    pending_trade: dict # For confirmation flow (None if no pending trade)

# Load Prompts
import yaml
PROMPTS = {}
try:
    with open("core/prompts/prompts.yaml", "r") as f:
        data = yaml.safe_load(f)
        PROMPTS = data.get("prompts", {})
except Exception as e:
    print(f"Failed to load prompts: {e}")
    # Fallback default
    PROMPTS = {
        "system_persona": "You are IRIS.",
        "extraction_template": "Extract trade...",
        "response_context_prefix": "Context:\n{context_data}",
        "trade_result_prefix": "Result: {trade_result}"
    }

# 2. Define the Nodes (Functions)
def classify_intent(state: AgentState):
    """Classifies user intent."""
    last_msg_obj = state['messages'][-1]
    last_msg_text = last_msg_obj.content if hasattr(last_msg_obj, 'content') else last_msg_obj[1]
    last_msg = last_msg_text.lower()
    
    # Check if we are waiting for confirmation
    pending = state.get('pending_trade')
    if pending:
        # Simple confirmation check
        if any(w in last_msg for w in ['yes', 'confirm', 'sure', 'do it', 'execute', 'ok']):
            return {"intent": "CONFIRM_TRADE"}
        elif any(w in last_msg for w in ['no', 'cancel', 'stop', 'don\'t']):
            return {"intent": "CANCEL_TRADE", "pending_trade": None} # Clear pending
        else:
            # User might be asking a question or changing subject
            # Let's pivot, but maybe keep pending? Or clear it? 
            # Safer to clear it if conversation drifts.
            return {"intent": "GENERAL_CHAT", "pending_trade": None}

    intent = "GENERAL_CHAT"
    if 'buy' in last_msg or 'sell' in last_msg or 'invest' in last_msg or 'execute' in last_msg:
        intent = 'TRADE'
    elif 'price' in last_msg or 'analyze' in last_msg or 'market' in last_msg or 'outlook' in last_msg:
        intent = 'ADVICE'
    elif 'risk' in last_msg or 'goal' in last_msg or 'portfolio' in last_msg or 'holdings' in last_msg:
        intent = 'ADVICE'
        
    return {"intent": intent}

def fetch_financial_data(state: AgentState):
    """Fetches real-time market data and RAG context."""
    user_id = state.get("user_id", "test-user")
    last_msg_obj = state['messages'][-1]
    text = last_msg_obj.content if hasattr(last_msg_obj, 'content') else last_msg_obj[1]
    
    # 1. Extract potential Ticker (Naïve)
    ticker = "SPY"
    words = text.split()
    for w in words:
        w_clean = w.strip(".,?!")
        if w_clean.isupper() and len(w_clean) <= 5 and w_clean.isalpha() and w_clean not in ["BUY", "SELL", "WHAT", "HOW", "WHY", "IS", "THE"]:
            ticker = w_clean
            break

    # 2. Fetch Context
    # Using the High-Speed Memory Store (Redis backed)
    user_personal_context = build_user_context(user_id)
    
    # Fetch dynamic data based on query
    market_data = get_market_data(ticker) 
    rag_context = lookup_rag_context(text)
    
    # 3. Aggregate
    full_context = f"""
    {user_personal_context}
    
    [Market Setup]
    {market_data}
    
    [Knowledge Base]
    {rag_context}
    """
    
    return {"tool_outputs": {"context_data": full_context}}

def execute_trade_node(state: AgentState):
    """Parses intent. If pending, decodes confirmation. If new, asks for confirmation."""
    intent = state.get("intent")
    
    # CASE 1: CONFIRMED execution
    if intent == "CONFIRM_TRADE":
        pending = state.get("pending_trade")
        if pending:
             # Execute
             raw_result = execute_trade_action(state.get("user_id", "test-user"), pending['symbol'], pending['action'], pending['quantity'], pending['amount'])
             
             # Calculate final details for the Prompt
             price = get_current_price(pending['symbol']) # Refetch or use stored estimate? Refetch for accuracy.
             total = price * pending['quantity']
             
             rich_result = (f"{raw_result}\n"
                            f"Details: Symbol={pending['symbol']}, Action={pending['action']}, "
                            f"Quantity={pending['quantity']}, Stats='Executed', "
                            f"Price Approx=${price:.2f}, Total Est=${total:.2f}")
                            
             return {"tool_outputs": {"trade_result": rich_result}, "pending_trade": None} # Clear
        else:
             return {"tool_outputs": {"trade_result": "Error: No pending trade found to confirm."}}

    # CASE 2: New Trade Request -> Extract & Ask Confirmation
    last_msg_obj = state['messages'][-1]
    text = last_msg_obj.content if hasattr(last_msg_obj, 'content') else last_msg_obj[1]
    
    extraction_prompt = PROMPTS.get("extraction_template", "").format(user_input=text)
    
    try:
        extraction_response = LLM.invoke(extraction_prompt)
        import json
        import re
        
        json_match = re.search(r'\{.*\}', extraction_response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            ticker = data.get("symbol")
            action = data.get("action", "buy")
            quantity = float(data.get("quantity", 0))
            amount = float(data.get("amount", 0))
            strategy = data.get("strategy", "")
            
            # Resolution logic (same as before)
            if not ticker or ticker == "null":
                # ... (Strategy logic omitted for brevity, keeping simple for this update) ...
                ticker = "SPY" 

            if quantity == 0 and amount > 0:
                price = get_current_price(ticker)
                if price > 0:
                    quantity = round(amount / price, 4)
            
            if quantity == 0:
                 quantity = 1 # Fallback
            
            # INSTEAD OF EXECUTING, WE SET PENDING STATE
            pending_trade = {
                "symbol": ticker,
                "action": action,
                "quantity": quantity,
                "amount": amount
            }
            
            # We return a specific tool output that tells the LLM to ask for confirmation
            price_est = get_current_price(ticker)
            total_est = price_est * quantity
            
            confirm_msg = f"Use this data to ask for confirmation: Proposed Trade: {action.upper()} {quantity} shares of {ticker} at approx ${price_est:.2f} (Total: ${total_est:.2f})."
            
            return {
                "pending_trade": pending_trade, 
                "tool_outputs": {"trade_result": confirm_msg} # Hijacking trade_result to pass info for prompt
            }
            
    except Exception as e:
        print(f"Extraction failed: {e}")

    return {"tool_outputs": {"trade_result": "Failed to understand trade details."}}

def generate_response(state: AgentState):
    """Generates the final response based on tool outputs."""
    tool_data = state.get("tool_outputs", {})
    
    system_prompt = PROMPTS.get("system_persona", "You are IRIS.")
    
    if "context_data" in tool_data:
        prefix = PROMPTS.get("response_context_prefix", "Context:\n{context_data}")
        system_prompt += "\n\n" + prefix.format(context_data=tool_data['context_data'])
        
    if "trade_result" in tool_data:
        prefix = PROMPTS.get("trade_result_prefix", "Result: {trade_result}")
        system_prompt += "\n\n" + prefix.format(trade_result=tool_data['trade_result'])
        
    formatted_msgs = [f"system: {system_prompt}"]
    for msg in state['messages']:
        if hasattr(msg, 'content'):
            role = msg.type
            content = msg.content
        else:
            role, content = msg
        formatted_msgs.append(f"{role}: {content}")
        
    full_prompt = "\n".join(formatted_msgs)
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
    if intent == 'TRADE' or intent == 'CONFIRM_TRADE':
        return "execute_trade"
    elif intent == 'ADVICE':
        return "fetch_data"
    else:
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
