"""
Medicine Pricing Agent Utilities
---------------------------------------------------------
Description: Tool definitions, system prompt, and tools list for the
             Medicine Pricing Agent. All helper functions and environment
             variables are self-contained within the tool definition.
"""

import os
import json
import re
import asyncio
from langchain_core.tools import tool


# ============================================================
# TOOL 1: Pharmacy Search Tool
# ============================================================

@tool
def pharmacy_search_tool(query: str) -> str:
    """
    Searches for live retail prices of medicines in India.
    Accepts complex medical lists, discharge summaries, or individual medicine names.

    Args:
        query: A comma-separated list of medicine names, a discharge summary excerpt,
               or any free-text description of medicines to look up.

    Returns:
        JSON string containing search results with pricing data from Indian pharmacies.
    """
    # ── env vars (self-contained) ──────────────────────────────
    from tavily import AsyncTavilyClient

    TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

    # ── helper: single-medicine search ────────────────────────
    async def _get_medicine_prices(client: AsyncTavilyClient, medicine: str):
        """
        Executes a deep search for a single pharmaceutical product.
        Structured to surface the most recent MRP and availability in India.
        """
        search_query = (
            f"current retail MRP price and availability of {medicine} in India in Rupees"
        )
        print(f"   [TAVILY API] Querying: '{search_query}'")
        try:
            response = await client.search(
                query=search_query,
                search_depth="advanced",
                max_results=10,
            )
            return {"medicine": medicine, "data": response["results"]}
        except Exception as e:
            return {"medicine": medicine, "error": str(e)}

    # ── helper: batch concurrent search ───────────────────────
    async def _run_batch_search(medicines: list):
        """
        Manages concurrent Tavily API calls for rapid multi-medicine processing.
        """
        client = AsyncTavilyClient(api_key=TAVILY_API_KEY)
        tasks = [_get_medicine_prices(client, med) for med in medicines]
        return await asyncio.gather(*tasks)

    # ── main tool logic ────────────────────────────────────────
    medicines = [
        m.strip(" ?.")
        for m in re.split(r",|\band\b|\n", query, flags=re.IGNORECASE)
        if m.strip(" ?.")
    ]
    print(f"\n[AGENT TOOL] Tool triggered for: {medicines}")

    results = asyncio.run(_run_batch_search(medicines))
    return json.dumps({"search_results": results}, indent=2)


# ============================================================
# SYSTEM PROMPT FOR MEDICINE AGENT
# ============================================================

MEDICINE_AGENT_SYSTEM_PROMPT = """You are a Senior Indian Clinical Pharmacist and Price Analyst.

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

STRICT WORKFLOW:
1. Call pharmacy_search_tool with the medicine name(s) or discharge summary text.
2. Parse the returned JSON search results.
3. Compile a structured pricing report following the output format below.

OUTPUT STRUCTURE:
- Provide one compact table per medication group.
- Columns: Source | Form | Price (₹) | Quantity | Unit Price | Link | Stock
- **Bold the lowest price** for the specific form factor requested.
- Include a 'Clinical/Generic Note' for each item mentioning Jan Aushadhi equivalents.

Rules:
- Only use data returned by pharmacy_search_tool.
- Never hallucinate prices, brands, or availability.
- Always mention generic/Jan Aushadhi alternatives where applicable.
- Flag any medicine that could not be priced due to search errors.
"""

# ============================================================
# TOOLS LIST FOR MEDICINE AGENT
# ============================================================

MEDICINE_AGENT_TOOLS = [
    pharmacy_search_tool,
]
