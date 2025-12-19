import yfinance as yf
import lancedb
import os
import requests

# --- CONFIGURATION ---
# LanceDB path must match the PVC mount in the K8s manifest
LANCE_DB_PATH = os.getenv("LANCE_DB_PATH", "/data/db/lancedb")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://iris-api-gateway:8080")

def safe_float(value):
    if isinstance(value, (int, float)):
        return float(value)
    try:
        if value is None or value == "":
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0

# --- CONTEXT RETRIEVAL TOOLS ---
def get_portfolio_details(user_id: str) -> str:
    """Fetches the user's current portfolio holdings and value."""
    try:
        url = f"{GATEWAY_URL}/v1/portfolio/{user_id}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Summarize for the LLM
            total_val = safe_float(data.get('totalValue'))
            # Use numeric raw values instead of formatted strings
            day_pl = safe_float(data.get('todayPLValue'))
            day_pl_pct = safe_float(data.get('todayPLPercent'))
            total_gl = safe_float(data.get('totalGainLoss'))
            total_gl_pct = safe_float(data.get('totalGainLossPercent'))
            
            summary = (f"Total Value: ${total_val:,.2f}. "
                       f"Today's Change: ${day_pl:,.2f} ({day_pl_pct:.2f}%). "
                       f"Total Gain/Loss: ${total_gl:,.2f} ({total_gl_pct:.2f}%).\n")
                       
            # Handle refactored data: check top-level holdings OR brokerGroups
            holdings = data.get('holdings') or []
            if not holdings:
                for group in data.get('brokerGroups', []):
                    group_holdings = group.get('holdings', [])
                    if group_holdings:
                        holdings.extend(group_holdings)

            if holdings:
                summary += "Holdings:\n"
                for h in holdings:
                    # Provide rich context for each holding
                    summary += (f"- {h['symbol']}: {h['shares']} shares @ ${safe_float(h['price']):.2f}. "
                                f"Value: ${safe_float(h['value']):,.2f}. "
                                f"Day Change: {safe_float(h['changePercent']):.2f}%. "
                                f"Total Gain: {safe_float(h['gainLossPercent']):.2f}% (${safe_float(h['gainLoss']):,.2f}).\n")
            else:
                summary += "No current holdings."
            return summary
        return "Could not fetch portfolio details."
    except Exception as e:
        return f"Error fetching portfolio: {e}"

def get_activity_log(user_id: str) -> str:
    """Fetches the user's recent transaction history."""
    try:
        url = f"{GATEWAY_URL}/v1/transactions/{user_id}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            txns = response.json()
            if not txns:
                return "No recent transactions."
            
            # Format as a list
            log_entries = []
            for t in txns:
                 log_entries.append(f"{t['timestamp'][:10]}: {t['type']} {t['shares']} {t['symbol']} @ ${t['price']:.2f}")
            return "Recent Activity: " + "; ".join(log_entries)
        return "Could not fetch transaction history."
    except Exception as e:
        return f"Error fetching transactions: {e}"

def get_past_conversations(user_id: str) -> str:
    """Fetches recent chat history for memory."""
    try:
        url = f"{GATEWAY_URL}/v1/chat/history/{user_id}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            history = response.json()
            if not history:
                return "" # Empty history is fine
            
            # Limit to last 5 exchanges to save tokens
            relevant_history = history[-10:] 
            formatted = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in relevant_history])
            return f"--- CHAT HISTORY ---\n{formatted}\n--- END HISTORY ---"
        return ""
    except Exception as e:
        print(f"Error fetching chat history: {e}")
        return ""

# --- CONFIGURATION ---
BROKER_SERVICE_URL = os.getenv("BROKER_SERVICE_URL", "http://iris-broker-service:8081")

# --- REDIS MEMORY STORE ---
import redis
import json

REDIS_ADDR = os.getenv("REDIS_ADDR", "redis:6379")
try:
    host, port = REDIS_ADDR.split(":")
    redis_client = redis.Redis(host=host, port=int(port), db=0, decode_responses=True)
except Exception as e:
    print(f"Redis connection failed: {e}")
    redis_client = None

def get_comprehensive_transactions(user_id: str, limit: int = 1000) -> str:
    """Fetches a comprehensive transaction history (up to limit) for RAG context."""
    try:
        url = f"{GATEWAY_URL}/v1/transactions/{user_id}?limit={limit}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            txns = response.json()
            if not txns:
                return "No recorded transactions."
            
            # Summarize or Format
            # For 10 years/1000 items, we might want to return a CSV-like block or a summary.
            # Let's return a compact list.
            lines = []
            for t in txns:
                 lines.append(f"{t['timestamp'][:10]} {t['type']} {t['shares']} {t['symbol']} @ ${t['price']:.2f}")
            return "\n".join(lines)
        return "Could not fetch transaction history."
    except Exception as e:
        return f"Error fetching transactions: {e}"

def build_user_context(user_id: str) -> str:
    """
    Builds a high-speed, cached User Context object containing:
    - Portfolio Summary
    - Recent Chat History
    - Comprehensive Transaction History
    """
    if not redis_client:
        return get_portfolio_details(user_id) # Fallback

    cache_key = f"user_context:{user_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return cached

    # Context Miss - Build it
    portfolio = get_portfolio_details(user_id)
    history = get_past_conversations(user_id)
    transactions = get_comprehensive_transactions(user_id, limit=1000)

    context = (f"--- USER CONTEXT (High-Speed Memory) ---\n"
               f"## PORTFOLIO\n{portfolio}\n\n"
               f"## TRANSACTION HISTORY (Last 1000)\n{transactions}\n\n"
               f"## CHAT HISTORY\n{history}\n"
               f"--- END CONTEXT ---")

    # Cache for 5 minutes (user active session)
    # We use setex for TTL
    redis_client.setex(cache_key, 300, context)
    
    return context

def get_alpaca_account_id(user_id: str) -> str:
    """Helper to find the Alpaca Account ID for the user."""
    # ... (existing logic, maybe we can cache this too?)
    # For now keep it simple.
    try:
        url = f"{GATEWAY_URL}/v1/portfolio/{user_id}"
        response = requests.get(url, timeout=5)
# ... rest of file
        if response.status_code == 200:
            data = response.json()
            # Look for the Alpaca/Core account
            # Based on API Gateway logic, we might need to identify it by BrokerName 'alpaca'
            # or we rely on the migration 'is_core' -> 'alpaca'
            
            # The Gateway returns 'brokerGroups'.
            groups = data.get('brokerGroups', [])
            for group in groups:
                 # Check for "Alpaca" or "Core"
                 # In migration we added name='alpaca'.
                 # Gateway logic maps broker_id to name.
                 if group.get('brokerName') == 'alpaca' or group.get('displayName') == 'Alpaca Markets' or group.get('portfolioType') == 'IRIS Core':
                     return group.get('irisAccountId') or group.get('accountNumber')
            
            # Fallback: if only one account or just return the first one?
            # Or maybe the user hasn't synced yet.
            if groups:
                return groups[0].get('accountNumber')
                
    except Exception as e:
        print(f"Error resolving account ID: {e}")
    return None

def execute_trade_action(user_id: str, ticker: str, action: str, quantity: float, price: float = 0.0) -> str:
    """Executes a trade via the Broker Service (Alpaca)."""
    
    # 1. Resolve Account ID
    account_id = get_alpaca_account_id(user_id)
    if not account_id:
        return "Error: No active brokerage account found for this user."

    # 2. Call Broker Service
    url = f"{BROKER_SERVICE_URL}/v1/trade"
    
    # Determine side
    side = "buy" if action.lower() == "buy" else "sell"
    
    payload = {
        "account_id": account_id,
        "symbol": ticker,
        "side": side,
        "qty": quantity,
        "type": "market", # Default to market for now
        "time_in_force": "day"
    }
    
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
        if response.status_code == 200:
            return f"Trade Order Submitted: {response.json()}"
        elif response.status_code == 202:
             return f"Trade Order Accepted for Processing: {response.json()}"
        else:
            return f"Trade failed with status {response.status_code}: {response.text}"
    except Exception as e:
        return f"Error executing trade on Broker Service: {e}"

# --- MARKET DATA TOOLS (Using Broker Service) ---
def get_current_price(ticker_symbol: str) -> float:
    """Returns the current price as a float for calculation purposes via Broker Service."""
    try:
        url = f"{BROKER_SERVICE_URL}/v1/quotes/{ticker_symbol}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # IEX quote has 'ap' (Ask Price) or 'bp'. Let's average or use one.
            # Struct: AskPrice, BidPrice.
            ask = data.get('ap', 0)
            bid = data.get('bp', 0)
            if ask > 0 and bid > 0:
                return (ask + bid) / 2
            return ask or bid or 0.0
        return 0.0
    except Exception as e:
        print(f"Error fetching price for {ticker_symbol}: {e}")
        return 0.0

def check_asset_availability(ticker_symbol: str) -> bool:
    """Checks if the asset is tradable via Broker Service."""
    try:
        url = f"{BROKER_SERVICE_URL}/v1/assets/{ticker_symbol}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("tradable", False)
        return False
    except Exception:
        return False

def get_market_data(ticker_symbol: str) -> str:
    """Retrieves current quote from Alpaca (Cached) via Broker Service."""
    try:
        if not ticker_symbol or ticker_symbol == "SPY":
            ticker_symbol = "SPY"
            
        # 1. Validation check (as requested)
        if not check_asset_availability(ticker_symbol):
             return f"Asset {ticker_symbol} is not available for trading or not found."

        # 2. Get Quote
        url = f"{BROKER_SERVICE_URL}/v1/quotes/{ticker_symbol}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
             data = response.json()
             ask = data.get('ap', 0)
             bid = data.get('bp', 0)
             price = ask or bid
             timestamp = data.get('t', 'N/A')
             
             return (f"Market Quote for {ticker_symbol} (Source: Alpaca IEX):\n"
                     f"Price: ${price:.2f} (Ask: ${ask:.2f}, Bid: ${bid:.2f})\n"
                     f"Disclaimer: Price quoted here is a snapshot for trade estimations. Actual trade prices can vary as the market prices change dynamically.")
        
        return f"Could not fetch market data for {ticker_symbol}."
    except Exception as e:
        return f"Error retrieving market data for {ticker_symbol}: {e}"

# --- LANCEDb RAG TOOL ---
def lookup_rag_context(query: str) -> str:
    """Looks up the most relevant industry knowledge from the LanceDB vector store."""
    try:
        # Connect to DB
        db = lancedb.connect(LANCE_DB_PATH)
        table_name = "financial_knowledge"
        
        if table_name not in db.table_names():
             return "Knowledge base not initialized."

        tbl = db.open_table(table_name)

        # Embed query (using same model as ingestion)
        # Note: In production, load model globally to avoid reload overhead
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        query_embedding = model.encode(query).tolist()

        # Search
        results = tbl.search(query_embedding).limit(2).to_pandas()
        
        if results.empty:
            return "No relevant context found."
            
        context = "Relevant Financial Context:\n"
        for _, row in results.iterrows():
            context += f"- [{row['title']}]: {row['text']}\n"
            
        return context

    except Exception as e:
        # Fail silently/gracefully for RAG to not block main chat
        print(f"LanceDB RAG retrieval error: {e}")
        return ""
        