"""
Medicine Price Comparison Agent - Web scraping for best prices
"""
from typing import List, Dict
from app.agents.base import BaseAgent, format_search_results
from app.scrapers.pharmacy import compare_prices, get_medicine_prices_tool


class MedicinePriceAgent(BaseAgent):
    """
    Agent for comparing medicine prices across pharmacies.
    
    Capabilities:
    - Search 1mg, Apollo Pharmacy, PharmEasy
    - Find cheapest option
    - Extract medicine names from discharge documents
    - Provide purchase links
    """
    
    SYSTEM_PROMPT = """You are a helpful pharmacy assistant who helps patients find 
the best prices for their medications. Your role is to:

1. Search multiple online pharmacies for medicine prices
2. Identify the cheapest and most convenient options
3. Help patients understand generic vs branded alternatives
4. Extract medicine names from their documents if needed

Important guidelines:
- Always provide price comparisons when possible
- Mention any caveats (prescription required, shipping time, etc.)
- Recommend buying from licensed pharmacies only
- Suggest consulting a doctor before switching brands"""

    def process(self, query: str) -> str:
        """
        Process a user query about medicine prices.
        """
        # Check if query mentions a specific medicine
        # If not, try to extract from discharge documents
        prompt = f"""Extract the medicine name from this query. 
If a specific medicine is mentioned, return just the medicine name.
If no medicine is mentioned, return "NONE".

Query: {query}

Medicine name:"""
        
        medicine_name = self.ask_llm(prompt).strip()
        
        if medicine_name == "NONE" or not medicine_name:
            # Try to help user identify medicines
            return self._suggest_medicines_from_discharge(query)
        
        # Search for prices
        return self._compare_prices(medicine_name, query)
    
    def _suggest_medicines_from_discharge(self, query: str) -> str:
        """Suggest medicine names from discharge documents."""
        results = self.search_discharge("medicine tablet capsule prescription", k=5)
        
        if not results:
            return """I couldn't find any medicines to search for. Please either:

1. Specify the medicine name: "Compare prices for Paracetamol 500mg"
2. Upload your discharge summary so I can extract medicine names
3. Ask me to find prices for a specific medication

Example queries:
- "What's the cheapest price for Metformin 500mg?"
- "Compare prices for my prescribed medicines"
- "Find best price for Atorvastatin 10mg" """
        
        context = format_search_results(results, include_source=False)
        
        prompt = f"""{self.SYSTEM_PROMPT}

## Discharge Document Content:
{context}

## Task:
Extract all medicine names mentioned in the documents above. 
List them in a format the patient can easily choose from:

1. [Medicine Name 1] - [Purpose if mentioned]
2. [Medicine Name 2] - [Purpose if mentioned]
...

Then ask which medicine the patient wants to compare prices for.

## Response:"""
        
        return self.ask_llm(prompt)
    
    def _compare_prices(self, medicine_name: str, original_query: str) -> str:
        """Compare prices across platforms."""
        # Get price comparison
        price_results = get_medicine_prices_tool(medicine_name)
        
        prompt = f"""{self.SYSTEM_PROMPT}

## Price Comparison Results:
{price_results}

## Patient's Query:
{original_query}

## Task:
Present the price comparison results in a clear, helpful format.
- Highlight the best deal
- Mention any important notes (generic alternatives, pack sizes)
- Provide actionable advice

## Response:"""
        
        return self.ask_llm(prompt)
    
    def compare_all_prescribed(self) -> str:
        """Compare prices for all medicines from discharge documents."""
        results = self.search_discharge("medicine tablet capsule prescription drug", k=8)
        
        if not results:
            return "No medicines found in your documents. Please upload your discharge summary."
        
        context = format_search_results(results, include_source=False)
        
        # Extract medicine names
        prompt = f"""From the following text, extract ONLY the medicine names 
(generic or brand names). Return as a comma-separated list.

Text:
{context}

Medicine names (comma-separated):"""
        
        medicines_str = self.ask_llm(prompt)
        medicines = [m.strip() for m in medicines_str.split(',') if m.strip()][:5]  # Limit to 5
        
        if not medicines:
            return "Could not extract medicine names from your documents."
        
        # Compare prices for each
        all_comparisons = []
        for med in medicines:
            price_result = get_medicine_prices_tool(med)
            all_comparisons.append(f"### {med}\n{price_result}")
        
        combined = "\n\n---\n\n".join(all_comparisons)
        
        summary_prompt = f"""{self.SYSTEM_PROMPT}

## Price Comparisons for All Prescribed Medicines:

{combined}

## Task:
Create a summary report with:
1. Quick comparison table of best prices
2. Total estimated cost from the cheapest platform
3. Any generic alternatives mentioned
4. Recommendation on where to purchase

## Summary Report:"""
        
        return self.ask_llm(summary_prompt)
