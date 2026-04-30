"""
Bill Validator Agent - Check hospital bills against regulations
"""
from typing import List, Dict
from app.agents.base import BaseAgent, format_search_results
from app.vectorstore.store import get_insurance_store


class BillValidatorAgent(BaseAgent):
    """
    Agent for validating hospital bills against NPPA and CGHS regulations.
    
    Capabilities:
    - Detect potential overcharging
    - Compare prices against NPPA ceiling prices
    - Compare against CGHS rates
    - Check insurance policy limits (room rent, co-pay)
    - Provide itemized analysis with citations
    """
    
    SYSTEM_PROMPT = """You are a healthcare billing expert who helps patients understand 
and validate their hospital bills. Your role is to:

1. Analyze hospital bill items for potential overcharging
2. Compare prices against government regulations (NPPA ceiling prices, CGHS rates)
3. Check against insurance policy limits (Room Rent Capping, Co-payment)
4. Identify specific items that may be overpriced or disallowed
5. Calculate potential savings
6. ALWAYS cite regulations and sources
Important guidelines:
- Be specific about which items are overpriced and by how much
- Quote the regulation name and ceiling price when available
- Suggest politely disputing overcharges
- Recommend keeping all bills for records
- Be factual and avoid speculation

Format responses clearly with tables and bullet points."""

    def process(self, query: str) -> str:
        """
        Process a user query about their hospital bill.
        
        Args:
            query: User's question about their bill
            
        Returns:
            Response with analysis and regulation citations
        """
        # Search user's bills
        bill_results = self.search_bills(query, k=5)
        
        # Search regulations for context
        reg_results = self.search_regulations(query, k=5)
        
        # Search insurance policies
        insurance_results = self.search_insurance(query, k=5)
        
        if not bill_results:
            return """I couldn't find any hospital bill documents to analyze.

Please upload your hospital bill PDF using the `/documents/upload/bill` endpoint.

Once uploaded, I can:
- Check for potential overcharging
- Compare prices against NPPA ceiling prices
- Compare against CGHS rates
- Identify items that may need to be disputed"""
        
        # Format context
        bill_context = format_search_results(bill_results)
        reg_context = format_search_results(reg_results) if reg_results else "No specific regulations found."
        ins_context = format_search_results(insurance_results) if insurance_results else "No specific policy clauses found."
        
        prompt = f"""{self.SYSTEM_PROMPT}

## Hospital Bill Items:
{bill_context}

## Relevant Regulations (NPPA/CGHS):
{reg_context}

## Insurance Policy Clauses:
{ins_context}

## Patient's Question:
{query}

## Instructions:
Analyze the bill items and answer the patient's question. If comparing prices:
- Quote the specific regulation and ceiling price
- Quote applicable insurance limits (room rent caps, etc.)
- Calculate the overcharge amount if applicable
- Suggest actions the patient can take

## Response:"""
        
        return self.ask_llm(prompt)
    
    def search_insurance(self, query: str, k: int = 5) -> List[Dict]:
        """Search shared insurance policies."""
        store = get_insurance_store()
        return store.search(query, k)

    def analyze_for_overcharging(self) -> str:
        """Perform comprehensive overcharging analysis on all bills."""
        # Search for common overcharged items
        categories = [
            "medicines drugs tablets",
            "consumables surgical supplies",
            "room charges bed",
            "doctor fees consultation",
            "laboratory tests",
            "procedure operation surgery",
        ]
        
        all_bill_items = []
        for cat in categories:
            results = self.search_bills(cat, k=3)
            all_bill_items.extend(results)
        
        # Deduplicate
        seen = set()
        unique_items = []
        for r in all_bill_items:
            h = hash(r['content'][:100])
            if h not in seen:
                seen.add(h)
                unique_items.append(r)
        
        if not unique_items:
            return "No bill items found for analysis. Please upload your hospital bill."
        
        # Get regulations and insurance
        reg_results = self.search_regulations("ceiling price NPPA CGHS rate", k=10)
        ins_results = self.search_insurance("room rent limit co-payment capping deduction", k=8)
        
        bill_context = format_search_results(unique_items[:10])
        reg_context = format_search_results(reg_results) if reg_results else "Regulations database not indexed yet."
        ins_context = format_search_results(ins_results) if ins_results else "Insurance policy not indexed yet."
        
        prompt = f"""{self.SYSTEM_PROMPT}

## Hospital Bill Items:
{bill_context}

## Applicable Regulations:
{reg_context}

## Insurance Policy Terms:
{ins_context}

## Task:
Perform a comprehensive overcharging analysis. Create a report with:

### 1. Potential Overcharges Identified
| Item | Bill Amount | Reg/Policy Limit | Overcharge | Source |
|------|-------------|------------------|------------|--------|
| ... | ₹... | ₹... | ₹... | NPPA/CGHS/Policy |

### 2. Policy Violations Check
- Room Rent Limits: Are room charges within policy limits?
- Co-payments: Any applicable co-pay?
- Non-Payables: Any items usually excluded?

### 3. Total Potential Overcharge
Sum of all identified overcharges.

### 3. Items That Appear Reasonable
Items within acceptable price ranges.

### 4. Recommendations
Steps the patient can take to dispute overcharges.

### 5. Disclaimer
Note that this is an automated analysis and professional review is recommended.

## Analysis Report:"""
        
        return self.ask_llm(prompt)
    
    def get_bill_breakdown(self) -> str:
        """Get a categorized breakdown of all bill items."""
        results = self.search_bills("charges amount rupees total", k=15)
        
        if not results:
            return "No bill items found. Please upload your hospital bill."
        
        context = format_search_results(results)
        
        prompt = f"""{self.SYSTEM_PROMPT}

## Bill Data:
{context}

## Task:
Create a categorized breakdown of the hospital bill:

### Bill Summary by Category

| Category | Amount (₹) | % of Total |
|----------|------------|------------|
| Room & Bed | ... | ... |
| Medicines | ... | ... |
| Consumables | ... | ... |
| Doctor Fees | ... | ... |
| Lab Tests | ... | ... |
| Procedures | ... | ... |
| Other | ... | ... |
| **Total** | **...** | **100%** |

### Observations
- Highest expense category
- Any unusual items
- Items to review

Cite sources and note any data that couldn't be extracted.

## Breakdown:"""
        
        return self.ask_llm(prompt)
