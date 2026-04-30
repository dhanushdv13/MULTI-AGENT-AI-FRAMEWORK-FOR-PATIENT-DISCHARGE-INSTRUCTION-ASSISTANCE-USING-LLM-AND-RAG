"""
Medicine Pricing Agent - Discharge Specialist
---------------------------------------------------------
Author: [Team]
Description: Professional-grade pharmaceutical price aggregator optimized
             for complex hospital discharge lists. Handles medical shorthand,
             specialty injectables, and multi-metric unit pricing.
"""

# uncomment this if you are running in colab
# import nest_asyncio
# nest_asyncio.apply()

import os
import json
import time
import re
import asyncio
from tavily import AsyncTavilyClient

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

# -------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
MODEL_NAME = os.environ.get("GEMINI_MODEL")

# -------------------------------------------------------------
# CORE SEARCH ENGINE
# -------------------------------------------------------------

async def get_medicine_prices(client: AsyncTavilyClient, medicine: str):
    """
    Executes deep search for pharmaceutical products.
    Query is structured to find the most recent MRP and availability in India.
    """
    search_query = f"current retail MRP price and availability of {medicine} in India in Rupees"
    
    print(f"   [TAVILY API] Querying: '{search_query}'")
    
    try:
        response = await client.search(
            query=search_query,
            search_depth="advanced",
            max_results=10 
        )
        return {"medicine": medicine, "data": response['results']}
    except Exception as e:
        return {"medicine": medicine, "error": str(e)}

async def run_batch_search(medicines: list):
    """
    Manages concurrent API calls to Tavily to ensure rapid multi-medicine processing.
    """
    client = AsyncTavilyClient(api_key=TAVILY_API_KEY)
    tasks = [get_medicine_prices(client, med) for med in medicines]
    return await asyncio.gather(*tasks)

# -------------------------------------------------------------
# AGENT TOOL DEFINITION
# -------------------------------------------------------------

@tool
def pharmacy_search_tool(query: str) -> str:
    """
    Searches for live retail prices of medicines in India. 
    Accepts complex medical lists, discharge summaries, or individual names.
    """
    medicines = [m.strip(" ?.") for m in re.split(r",|\band\b|\n", query, flags=re.IGNORECASE) if m.strip(" ?.")]
    print(f"\n[AGENT TOOL] Tool triggered for: {medicines}")
    results = asyncio.run(run_batch_search(medicines))    
    return json.dumps({"search_results": results}, indent=2)

# -------------------------------------------------------------
# SYSTEM PROMPT (Discharge Summary Optimized)
# -------------------------------------------------------------

PRO_PROMPT = """You are a Senior Indian Clinical Pharmacist and Price Analyst.

OBJECTIVE:
Analyze search data for a list of medications, often provided in hospital discharge format. 

CORE COMPETENCIES:
1. SHORTHAND PARSING: Understand 'Tab.' (Tablet), 'Inj.' (Injection), 'Syr.' (Syrup), 'MDI' (Inhaler), and 'Pen' (Insulin).
2. MULTI-CATEGORY UNIT PRICING:
   - Oral Solids: Price per tablet.
   - Liquids/Syrups: Price per 100ml.
   - Inhalers/Sprays: Price per Metered Dose (MDI) or per ml.
   - Injectables/Insulin: Price per unit or per pen.
3. RETAIL PURIFICATION: Filter out Indiamart/TradeIndia (Wholesale) and international (USD) pricing.

OUTPUT STRUCTURE:
- Provide one compact table per medication group.
- Columns: Source | Form | Price (₹) | Quantity | Unit Price | Link | Stock
- **Bold the lowest price** for the specific form factor requested.
- Include a 'Clinical/Generic Note' for each item mentioning Jan Aushadhi equivalents.
"""

# Initialize Agent
llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0)
agent = create_agent(model=llm, tools=[pharmacy_search_tool], system_prompt=PRO_PROMPT)

# -------------------------------------------------------------
# EXECUTION INTERFACE
# -------------------------------------------------------------

if __name__ == "__main__":
    print("-" * 60)
    print("Medicine Pricing Agent ")
    print("-" * 60)
    
    while True:
        try:
            user_input = input("\n Enter Medicine/s: ").strip()
            
            if not user_input or user_input.lower() in ["exit", "quit"]:
                break
            
            print(f"[SYSTEM] Parsing clinical data and searching...")
            
            response = agent.invoke({"messages": [HumanMessage(content=user_input)]})
            
            content = response["messages"][-1].content
            print("\n" + "=" * 60)
            print(content if isinstance(content, str) else "".join([b.get("text", "") for b in content]))
            print("=" * 60)
            
        except Exception as e:
            print(f"\n[ERROR] {e}")