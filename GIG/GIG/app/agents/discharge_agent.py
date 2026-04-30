"""
Discharge Summary Agent - RAG-based analysis of discharge documents
"""
from typing import List, Dict
from app.agents.base import BaseAgent, format_search_results


class DischargeSummaryAgent(BaseAgent):
    """
    Agent for analyzing discharge summaries.
    
    Capabilities:
    - Explain diagnoses in simple terms
    - List medications with purposes
    - Summarize treatment and procedures
    - Explain follow-up instructions
    """
    
    SYSTEM_PROMPT = """You are a helpful medical assistant specializing in explaining 
discharge summaries to patients. Your role is to:

1. Explain medical terms in simple, easy-to-understand language
2. Provide clear summaries of diagnoses, treatments, and medications
3. Highlight important follow-up instructions
4. ALWAYS cite the source document when providing information

Important guidelines:
- Be empathetic and reassuring
- Avoid causing unnecessary alarm
- Recommend consulting a doctor for medical advice
- Always mention page numbers and document sources
- If information is not found in the documents, say so clearly

Format your responses clearly with headers and bullet points."""

    def process(self, query: str) -> str:
        """
        Process a user query about their discharge summary.
        
        Args:
            query: User's question about their discharge
            
        Returns:
            Response with explanation and citations
        """
        # Search discharge documents
        results = self.search_discharge(query, k=5)
        
        if not results:
            return """I couldn't find any discharge summary documents to answer your question.

Please make sure you have uploaded your discharge summary PDF. You can upload it using the 
`/documents/upload/discharge` endpoint.

Once uploaded, I'll be able to help you understand your diagnosis, medications, and 
follow-up instructions."""
        
        # Format context
        context = format_search_results(results)
        
        # Build prompt
        prompt = f"""{self.SYSTEM_PROMPT}

## Patient's Discharge Documents:
{context}

## Patient's Question:
{query}

## Instructions:
Based on the discharge documents above, answer the patient's question. 
Be thorough but easy to understand. Always cite the source (filename and page).
If the information isn't in the documents, clearly state that.

## Response:"""
        
        # Get LLM response
        response = self.ask_llm(prompt)
        
        return response
    
    def get_summary(self) -> str:
        """Get a comprehensive summary of all discharge documents."""
        # Search for key topics
        topics = ["diagnosis", "medications", "procedures", "follow-up", "diet", "restrictions"]
        
        all_results = []
        for topic in topics:
            results = self.search_discharge(topic, k=3)
            all_results.extend(results)
        
        if not all_results:
            return "No discharge documents found. Please upload your discharge summary."
        
        # Deduplicate by content
        seen = set()
        unique_results = []
        for r in all_results:
            content_hash = hash(r['content'][:100])
            if content_hash not in seen:
                seen.add(content_hash)
                unique_results.append(r)
        
        context = format_search_results(unique_results[:10])
        
        prompt = f"""{self.SYSTEM_PROMPT}

## Discharge Documents:
{context}

## Task:
Create a comprehensive summary of the patient's discharge documents. Include:

1. **Diagnosis**: What condition(s) were treated
2. **Treatment Summary**: Key procedures or treatments performed
3. **Medications**: List all prescribed medications with their purposes
4. **Follow-up Instructions**: Appointments, tests, or actions needed
5. **Dietary/Lifestyle Recommendations**: Any restrictions or recommendations
6. **Warning Signs**: Symptoms that require immediate medical attention

Format the response clearly with headers. Always cite sources.

## Summary:"""
        
        return self.ask_llm(prompt)
    
    def extract_medications(self) -> str:
        """Extract and explain all medications from discharge documents."""
        results = self.search_discharge("medications prescribed medicine tablet capsule syrup", k=8)
        
        if not results:
            return "No medication information found in your documents."
        
        context = format_search_results(results)
        
        prompt = f"""{self.SYSTEM_PROMPT}

## Discharge Documents (Medication sections):
{context}

## Task:
Extract ALL medications mentioned in the documents. For each medication, provide:

| Medication Name | Dosage | Frequency | Purpose |
|----------------|--------|-----------|---------|
| ... | ... | ... | ... |

After the table, briefly explain any important precautions or interactions 
the patient should know about. Cite sources.

## Medications List:"""
        
        return self.ask_llm(prompt)
