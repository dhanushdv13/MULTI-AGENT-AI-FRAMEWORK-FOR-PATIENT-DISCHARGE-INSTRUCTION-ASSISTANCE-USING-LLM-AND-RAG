# DISCHARGE_AGENT_TOOLS=[]
# DISCHARGE_AGENT_SYSTEM_PROMPT="""
#     You are a helpful agent
# """

"""
Discharge Agent - RAG-based discharge summary specialist
"""

from typing import Dict
from pathlib import Path
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_community.vectorstores import FAISS
from rag import embed_instance
from model import llm

# ============================================================
# CONFIG
# ============================================================

VECTOR_STORES_DIR = Path("vectorstores")

embeddings = embed_instance.get_embeddings()


# ============================================================
# TOOL 1: Structured Discharge Info Extractor
# ============================================================

@tool
def extract_discharge_info(kb_name: str) -> Dict[str, str]:
    """
    Extracts structured discharge summary information from KB.

    Returns:
        - Patient Information
        - Admission Details
        - Final Diagnosis
        - Hospital Course Summary
        - Procedures Performed
        - Medications at Discharge
        - Follow-up Instructions
    """

    try:
        kb_path = VECTOR_STORES_DIR / kb_name

        if not kb_path.exists():
            return {"error": f"KB not found at {kb_path}"}

        kb = FAISS.load_local(
            str(kb_path),
            embeddings,
            allow_dangerous_deserialization=True
        )

        retriever = kb.as_retriever(search_kwargs={"k": 4})

        structured_questions = {
            # 🆕 PATIENT INFO
            "Patient Information": """
Extract:
- Patient Name
- Age
- Gender
- UHID / MRN
- Hospital Name
""",

            "Admission Details": """
Extract:
- Date of Admission
- Date of Discharge
- Length of Stay (if available)
- Treating Doctor
""",

            # Clinical Sections
            "Final Diagnosis": "What is the final diagnosis mentioned?",
            "Hospital Course Summary": "Summarize the hospital course.",
            "Procedures Performed": "What procedures or surgeries were performed?",
            "Medications at Discharge": "What medications were prescribed at discharge?",
            "Follow-up Instructions": "What follow-up advice or precautions were given?"
        }

        results = {}

        for section, question in structured_questions.items():
            docs = retriever.invoke(question)
            context = "\n".join([doc.page_content for doc in docs])

            prompt = f"""
You are a medical documentation assistant.

Extract the following section from discharge summary.

SECTION: {section}

Instructions:
- Extract ONLY what is present in context.
- If information is missing, write "Not Mentioned".
- Provide structured bullet points.

Context:
{context}
"""

            response = llm.invoke(prompt)
            results[section] = response.content.strip()

        return results

    except Exception as e:
        return {"error": f"Extraction failed: {str(e)}"}



# ============================================================
# TOOL 2: Additional Discharge Q&A Tool
# ============================================================

@tool
def discharge_query_tool(query: str, kb_name: str) -> str:
    """
    Answers additional user-specific discharge questions using KB.
    """

    try:
        kb_path = VECTOR_STORES_DIR / kb_name

        if not kb_path.exists():
            return f"ERROR: KB not found at {kb_path}"

        kb = FAISS.load_local(
            str(kb_path),
            embeddings,
            allow_dangerous_deserialization=True
        )

        retriever = kb.as_retriever(search_kwargs={"k": 5})
        docs = retriever.invoke(query)

        context = "\n\n".join([doc.page_content for doc in docs])

        prompt = f"""
You are a clinical discharge assistant.

Use ONLY the context below to answer the question.
Do not hallucinate.

Question:
{query}

Context:
{context}
"""

        response = llm.invoke(prompt)
        answer = response.content.strip()

        citations = "\n".join([
            f"- {doc.metadata.get('source', 'discharge_kb')} (Page: {doc.metadata.get('page', 'N/A')})"
            for doc in docs
        ])

        return f"""
{answer}

══════════════════════════════
CITATIONS:
══════════════════════════════
{citations}
"""

    except Exception as e:
        return f"ERROR: {str(e)}"


# ============================================================
# SYSTEM PROMPT
# ============================================================

DISCHARGE_AGENT_SYSTEM_PROMPT = """
You are the Discharge Summary Specialist.

STRICT WORKFLOW:

If user asks:
- "Give discharge summary"
- "Explain discharge"
- "Extract discharge details"
- "What happened during admission?"

→ Call extract_discharge_info with kb_name.

If user asks specific additional questions like:
- "Why was aspirin given?"
- "What was my blood sugar?"
- "Explain creatinine levels"
- "Was any surgery performed?"

→ Call discharge_query_tool with:
   - query
   - kb_name

Rules:
- Always rely on KB evidence.
- Never hallucinate.
- Be medically cautious.
- Provide clear bullet points when extracting sections.
"""


# ============================================================
# TOOL LIST
# ============================================================

DISCHARGE_AGENT_TOOLS = [
    extract_discharge_info,
    discharge_query_tool
]