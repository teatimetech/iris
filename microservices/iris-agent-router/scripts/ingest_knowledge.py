
import lancedb
import os
import pandas as pd
from sentence_transformers import SentenceTransformer

# Configuration
LANCE_DB_PATH = os.getenv("LANCE_DB_PATH", "/data/db/lancedb")
MODEL_NAME = "all-MiniLM-L6-v2"

# Mock Financial Data (In a real app, this would come from PDFs/Web Scraping)
documents = [
    {
        "title": "Market Outlook Q2 2024",
        "text": "Inflation is showing signs of moderating, with the CPI cooling to 3.1%. The Federal Reserve has signaled potential rate cuts later in the year, which could boost growth stocks, particularly in the technology sector. However, geopolitical risks remain a concern for energy markets.",
        "category": "Market Outlook"
    },
    {
        "title": "Tech Sector Analysis",
        "text": "The technology sector continues to be driven by AI adoption. Companies like NVIDIA and Microsoft are leading the charge. Cloud computing growth remains robust, although enterprise spending is being scrutinized. Semiconductor demand is outstripping supply.",
        "category": "Sector Analysis"
    },
    {
        "title": "Defensive Strategy",
        "text": "In times of volatility, defensive sectors like Healthcare and Consumer Staples tend to outperform. Dividend aristocrats provide a buffer against market downturns. Bonds are becoming attractive again as yields stabilize.",
        "category": "Strategy"
    },
    {
        "title": "Crypto Market Update",
        "text": "Bitcoin has seen a resurgence following the approval of Spot ETFs. Institutional adoption is increasing, but regulatory clarity is still evolving. Ethereum's upgrade promises lower fees and faster transaction times.",
        "category": "Crypto"
    }
]

def ingest():
    print(f"Connecting to LanceDB at {LANCE_DB_PATH}...")
    db = lancedb.connect(LANCE_DB_PATH)
    
    print(f"Loading embedding model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    
    # Prepare data
    print("Embedding documents...")
    data = []
    for doc in documents:
        embedding = model.encode(doc["text"]).tolist()
        data.append({
            "vector": embedding,
            "text": doc["text"],
            "title": doc["title"],
            "category": doc["category"]
        })
    
    # Create Table
    table_name = "financial_knowledge"
    try:
        if table_name in db.table_names():
            print(f"Table {table_name} exists. Overwriting...")
            db.drop_table(table_name)
        
        print(f"Creating table {table_name}...")
        tbl = db.create_table(table_name, data)
        print(f"Successfully ingested {len(data)} documents into {table_name}.")
        
    except Exception as e:
        print(f"Error during ingestion: {e}")

if __name__ == "__main__":
    # Ensure directory exists
    os.makedirs(LANCE_DB_PATH, exist_ok=True)
    ingest()
