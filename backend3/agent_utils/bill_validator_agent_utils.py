from typing import Dict, Any
import json
from pathlib import Path
from langchain.tools import tool
from langchain_community.vectorstores import FAISS
from rag import embed_instance
from model import llm


# ============================================================
# PATHS
# ============================================================

VECTOR_STORES_DIR = Path("vectorstores")

# Reference KBs
CGHS_KB_PATH = str(VECTOR_STORES_DIR / "cghs_rates")
NPPA_KB_PATH = str(VECTOR_STORES_DIR / "nppa_prices")

# Embeddings
embeddings = embed_instance.get_embeddings()


# ============================================================
# TOOL 1: Extract Bill Items
# ============================================================

@tool
def extract_bill_items(kb_name: str) -> str:
    """
    Extracts structured billing items from hospital bill KB.

    Args:
        kb_name: Name of the bill vectorstore.

    Returns:
        JSON containing:
        - procedures
        - medicines
        - room_charges
        - icu_charges
        - investigations
    """

    try:

        kb_path = str(VECTOR_STORES_DIR / kb_name)

        if not Path(kb_path).exists():
            return json.dumps({"error": f"Bill KB not found: {kb_path}"})

        bill_kb = FAISS.load_local(
            kb_path,
            embeddings,
            allow_dangerous_deserialization=True
        )

        retriever = bill_kb.as_retriever(search_kwargs={"k": 10})

        query = """
Extract all billable items from this hospital bill.

Return structured JSON with:

procedures
investigations
medicines
room_charges
icu_charges

Each item must include:
name
quantity
charged_price
"""

        docs = retriever.invoke(query)

        context = "\n\n".join([doc.page_content for doc in docs])

        prompt = f"""
You are a medical billing auditor. Extract EVERY charge from the bill context.

Context:
{context}

Return STRICT JSON format:
{{
"procedures": [],
"investigations": [],
"medicines": [],
"room_charges": [],
"icu_charges": [],
"miscellaneous_charges": [], 
"bill_summary": {{
    "subtotal": 0,
    "taxes": 0,
    "grand_total": 0
  }}
}}

Note: Include Nursing Care and Dressing/Consumables in 'miscellaneous_charges'. 
Ensure 'grand_total' matches the final amount printed on the bill.
"""
        response = llm.invoke(prompt)
        return response.content.strip()

    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================
# TOOL 2: Validate All Charges (CGHS + NPPA combined)
# Merged to avoid parallel tool calls that cause MALFORMED_FUNCTION_CALL
# ============================================================

@tool
def validate_all_charges(
    procedures: str,
    investigations: str,
    room_charges: str,
    icu_charges: str,
    medicines: str,
    miscellaneous_charges: str = "[]" # New parameter
) -> str:
    """
    Validates ALL hospital charges including miscellaneous items against CGHS/NPPA.
    """
    result = {}

    # ── CGHS validation ──────────────────────────────────────
    try:
        if not Path(CGHS_KB_PATH).exists():
            result["procedure_validation"] = "ERROR: CGHS KB not found"
        else:
            cghs_kb = FAISS.load_local(CGHS_KB_PATH, embeddings, allow_dangerous_deserialization=True)
            retriever = cghs_kb.as_retriever(search_kwargs={"k": 10})

            # Include Misc charges in the search query for CGHS rates
            query = f"Rates for: {procedures}, {investigations}, {room_charges}, {icu_charges}, {miscellaneous_charges}"
            docs = retriever.invoke(query)
            context = "\n\n".join([doc.page_content for doc in docs])

            prompt = f"""
You are a hospital billing auditor. Compare these hospital charges against CGHS reference rates.
If an item (like Nursing or Dressing) is in the miscellaneous list, check for its CGHS code as well.

Context (CGHS Rates):
{context}

Hospital Charges to Validate:
Procedures: {procedures}
Investigations: {investigations}
Room/ICU: {room_charges} / {icu_charges}
Misc: {miscellaneous_charges}

Return JSON array of objects:
{{
  "item": "",
  "charged_price": "",
  "allowed_price": "",
  "status": "VALID / OVERPRICED / UNDERPRICED / NO RATE FOUND",
  "excess_amount": 0
}}
"""
            response = llm.invoke(prompt)
            result["procedure_validation"] = response.content.strip()

    except Exception as e:
        result["procedure_validation"] = f"ERROR: {str(e)}"

    # ── NPPA validation (Medicine logic remains same but improved prompt) ────────
    try:
        if not Path(NPPA_KB_PATH).exists():
            result["medicine_validation"] = "ERROR: NPPA KB not found"
        else:
            nppa_kb = FAISS.load_local(NPPA_KB_PATH, embeddings, allow_dangerous_deserialization=True)
            retriever = nppa_kb.as_retriever(search_kwargs={"k": 5})
            
            docs = retriever.invoke(f"Ceiling prices for: {medicines}")
            context = "\n\n".join([doc.page_content for doc in docs])

            prompt = f"""
You are a pharmaceutical pricing auditor. Validate against NPPA ceiling prices.
Context: {context}
Medicines: {medicines}

Return JSON array:
[{{"medicine": "", "charged_price": "", "allowed_price": "", "status": "", "excess_amount": ""}}]
"""
            response = llm.invoke(prompt)
            result["medicine_validation"] = response.content.strip()

    except Exception as e:
        result["medicine_validation"] = f"ERROR: {str(e)}"

    return json.dumps(result)


# ============================================================
# TOOL 3: Generate Final Audit Report
# ============================================================

@tool
def generate_bill_validation_report(
    procedure_validation: str,
    medicine_validation: str
) -> str:
    """
    Generates final bill audit report.
    """

    prompt = f"""
You are a hospital billing audit expert.

Procedure Validation:
{procedure_validation}

Medicine Validation:
{medicine_validation}

Generate final report including:

1. Summary
2. Overpriced Items
3. Valid Items
4. Estimated Excess Billing
5. Recommendation

Be concise and structured.
"""

    response = llm.invoke(prompt)

    return response.content.strip()


BILL_VALIDATOR_SYSTEM_PROMPT = """
You are the Hospital Bill Validation Agent.

Your job is to detect overpricing in hospital bills using
CGHS (Central Government Health Scheme) rate rules and NPPA medicine ceiling prices.

STRICT WORKFLOW — follow EXACTLY in order, one step at a time:

Step 1:
Call 'extract_bill_items' with the bill KB name. 
This tool will extract all items, miscellaneous charges (like Nursing/Dressing), and the bill summary (Grand Total and taxes).
Wait for the result before proceeding.

Step 2:
Parse the JSON output from Step 1.
Call 'validate_all_charges' with ALL SIX arguments:
- procedures             ← from extract_bill_items output
- investigations        ← from extract_bill_items output
- room_charges          ← from extract_bill_items output
- icu_charges           ← from extract_bill_items output
- medicines             ← from extract_bill_items output
- miscellaneous_charges ← from extract_bill_items output (includes Nursing, Dressing, etc.)
Wait for the result before proceeding.

Step 3:
Parse the JSON output from Step 2.
Call 'generate_bill_validation_report' with:
- procedure_validation ← value of "procedure_validation" key from Step 2
- medicine_validation  ← value of "medicine_validation" key from Step 2

Rules:
- Always call tools ONE AT A TIME, strictly in order.
- Never call two tools simultaneously.
- Always rely on knowledge base evidence; never invent prices.
- TOTAL BILL: When asked for the total bill, always refer to the 'grand_total' found in the 'bill_summary' from Step 1. Do not try to sum the items manually, as you might miss taxes (GST) or service charges.
- MISCELLANEOUS: Ensure items like 'Nursing Care' and 'Dressing' are passed to the validation tool so they can be checked against CGHS codes.
- Clearly mark items as VALID, OVERPRICED, or NO RATE FOUND.
- The final report must be provided at the end of the conversation, even if no overcharging was detected.
"""

# ============================================================
# TOOL LIST
# ============================================================

BILL_VALIDATOR_TOOLS = [
    extract_bill_items,
    validate_all_charges,
    generate_bill_validation_report
]
