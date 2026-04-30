from typing import Dict, Any
import json
from pathlib import Path
from langchain.tools import tool
from langchain_community.vectorstores import FAISS
from rag import embed_instance
from model import llm

VECTOR_STORES_DIR = Path("vectorstores")
DIET_KB_PATH = str(VECTOR_STORES_DIR / "diet_docs")

# Initialize embedding manager
embeddings = embed_instance.get_embeddings()


# ============================================================
# TOOL 1: Extract Medical Info from Discharge KB
# ============================================================

@tool
def extract_medical_info(kb_name: str) -> str:
    """
    Loads discharge summary FAISS vectorstore and extracts medical information.

    Args:
        kb_name: Name of the KB

    Returns:
        JSON string containing:
        - Diagnoses
        - Medical Conditions
        - Prescribed Medications
        - Dietary Restrictions
        - Recovery Notes
    """
    try:
        # Load the FAISS vectorstore based on the kb_name
        kb_path = str(VECTOR_STORES_DIR / kb_name)
        
        if not Path(kb_path).exists():
            return json.dumps({
                "error": f"KB '{kb_name}' not found at {kb_path}",
                "Diagnoses": "",
                "Medical Conditions": "",
                "Prescribed Medications": "",
                "Dietary Restrictions": "",
                "Recovery Notes": ""
            })
        
        # Load FAISS vectorstore
        kb = FAISS.load_local(
            kb_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
        
        # Define medical info categories to extract
        medical_categories = [
            "Diagnoses",
            "Medical Conditions",
            "Prescribed Medications",
            "Dietary Restrictions",
            "Recovery Notes"
        ]
        
        # Extract information for each category
        medical_info = {}
        
        for category in medical_categories:
            # Query the vectorstore for each category
            query = f"What are the {category.lower()} mentioned in the {kb_name}?"
            retriever = kb.as_retriever(search_kwargs={"k": 3})
            docs = retriever.invoke(query)
            
            # Combine retrieved content
            context = "\n".join([doc.page_content for doc in docs])
            
            # Use LLM to extract structured information
            extraction_prompt = f"""
Based on the following {kb_name} context, extract the {category}.
Provide a clear, concise bullet-point list.

Context:
{context}

{category}:
"""
            response = llm.invoke(extraction_prompt)
            medical_info[category] = response.content.strip()
        
        return json.dumps(medical_info)

    except Exception as e:
        return json.dumps({
            "error": f"Failed to extract medical info: {str(e)}",
            "Diagnoses": "",
            "Medical Conditions": "",
            "Prescribed Medications": "",
            "Dietary Restrictions": "",
            "Recovery Notes": ""
        })


# ============================================================
# TOOL 2: Get Diet Recommendations from Diet KB
# ============================================================

@tool
def get_diet_recommendations(
    diagnoses: str,
    medical_conditions: str,
    prescribed_medications: str,
    dietary_restrictions: str,
    recovery_notes: str,
) -> str:
    """
    Queries diet KB vectorstore with medical information and returns
    diet recommendations with citations.

    Args:
        diagnoses: Diagnoses field from extract_medical_info.
        medical_conditions: Medical Conditions field from extract_medical_info.
        prescribed_medications: Prescribed Medications field from extract_medical_info.
        dietary_restrictions: Dietary Restrictions field from extract_medical_info.
        recovery_notes: Recovery Notes field from extract_medical_info.
    """

    try:
        # Check if diet KB exists
        if not Path(DIET_KB_PATH).exists():
            return f"ERROR: Diet KB not found at {DIET_KB_PATH}. Please run 'python build_vector_stores.py'"

        # Load FAISS vectorstore
        diet_kb = FAISS.load_local(
            DIET_KB_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )

        # Create retriever
        retriever = diet_kb.as_retriever(search_kwargs={"k": 5})

        # Construct query
        query = f"""
Based on the following medical information, provide diet recommendations:

Diagnoses: {diagnoses}
Medical Conditions: {medical_conditions}
Prescribed Medications: {prescribed_medications}
Dietary Restrictions: {dietary_restrictions}
Recovery Notes: {recovery_notes}
"""

        # Retrieve documents manually
        docs = retriever.invoke(query)

        # Combine retrieved content
        context = "\n\n".join([doc.page_content for doc in docs])

        # Build final prompt
        final_prompt = f"""
You are a clinical dietitian.

Use ONLY the provided knowledge base context to answer.

Medical Information:
Diagnoses: {diagnoses}
Medical Conditions: {medical_conditions}
Prescribed Medications: {prescribed_medications}
Dietary Restrictions: {dietary_restrictions}
Recovery Notes: {recovery_notes}

Knowledge Base Context:
{context}

Provide:
1. Foods to consume (with portion sizes)
2. Foods to avoid
3. Medication-food interactions
4. Indian cuisine meal plan (Breakfast, Lunch, Dinner)
5. Hydration advice
6. Recovery precautions

Do NOT hallucinate outside the context.
"""

        # Call LLM manually
        response = llm.invoke(final_prompt)
        answer = response.content.strip()

        # Format citations
        citations = []
        for doc in docs:
            citations.append({
                "source": doc.metadata.get("source", "diet_kb"),
                "page": doc.metadata.get("page", "N/A")
            })

        citation_text = "\n".join([
            f"- {c['source']} (Page: {c['page']})"
            for c in citations
        ])

        return f"""
{answer}

═══════════════════════════════════════════════════
CITATIONS:
═══════════════════════════════════════════════════
{citation_text}
"""

    except Exception as e:
        return f"ERROR: Failed to get diet recommendations: {str(e)}"


# ============================================================
# SYSTEM PROMPT FOR DIET AGENT
# ============================================================

DIET_AGENT_SYSTEM_PROMPT = """
You are the Diet & Nutrition Agent.

STRICT WORKFLOW:
1. Call extract_medical_info with the kb_name argument.
2. The tool returns a JSON string. Parse it and call get_diet_recommendations
   with these FIVE arguments extracted from the JSON:
   - diagnoses         ← value of "Diagnoses" key
   - medical_conditions ← value of "Medical Conditions" key
   - prescribed_medications ← value of "Prescribed Medications" key
   - dietary_restrictions   ← value of "Dietary Restrictions" key
   - recovery_notes         ← value of "Recovery Notes" key

Rules:
- Always rely on KB evidence.
- Never hallucinate diet advice.
- Prefer Indian cuisine unless specified.
- Mention portion sizes.
- Mention medication-food interactions.
- Be medically cautious.
"""

# ============================================================
# TOOLS LIST FOR DIET AGENT
# ============================================================

DIET_AGENT_TOOLS = [
    extract_medical_info,
    get_diet_recommendations
]
