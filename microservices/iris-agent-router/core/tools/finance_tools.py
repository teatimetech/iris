import yfinance as yf
import lancedb
import os
import requests

# --- CONFIGURATION ---
# LanceDB path must match the PVC mount in the K8s manifest
LANCE_DB_PATH = os.getenv("LANCE_DB_PATH", "/data/db/lancedb")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://iris-api-gateway:8080")

# --- CONTEXT RETRIEVAL TOOLS ---
def get_portfolio_details(user_id: str) -> str:
    """Fetches the user's current portfolio holdings and value."""
    try:
        url = f"{GATEWAY_URL}/v1/portfolio/{user_id}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Summarize for the LLM
            summary = f"Total Value: ${data.get('totalValue', 0):.2f}. "
            holdings = data.get('holdings', [])
            if holdings:
                summary += "Holdings: " + ", ".join([f"{h['symbol']} ({h['shares']} shares @ ${h['price']:.2f})" for h in holdings])
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

# --- TRADE TOOL ---
def execute_trade_action(user_id: str, ticker: str, action: str, quantity: float, price: float) -> str:
    """Executes a trade via the API Gateway."""
    url = f"{GATEWAY_URL}/v1/trade"
    payload = {
        "user_id": user_id,
        "symbol": ticker,
        "action": action,   # "BUY" or "SELL"
        "shares": quantity,
        "price": price
    }
    
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=5)
        if response.status_code == 200:
            return f"Trade executed successfully: {response.json()}"
        else:
            return f"Trade failed with status {response.status_code}: {response.text}"
    except Exception as e:
        return f"Error executing trade: {e}"

# --- YFINANCE TOOL ---
def get_market_data(ticker_symbol: str) -> str:
    """Retrieves current price and 5-day performance summary from yfinance."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        history = ticker.history(period="5d")
        
        if history.empty:
             return f"No market data found for {ticker_symbol}."

        current_price = history['Close'].iloc[-1]
        five_day_change = (current_price / history['Close'].iloc[0] - 1) * 100
        
        return f"Current Price of {ticker_symbol}: ${current_price:.2f}. 5-day change: {five_day_change:.2f}%."
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
        