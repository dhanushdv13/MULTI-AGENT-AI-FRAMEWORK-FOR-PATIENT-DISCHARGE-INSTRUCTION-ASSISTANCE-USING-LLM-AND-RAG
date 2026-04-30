"""
Diet Planning Agent - Personalized nutrition based on medical conditions
"""
from typing import List, Dict
from app.agents.base import BaseAgent, format_search_results


class DietPlanningAgent(BaseAgent):
    """
    Agent for creating personalized diet plans.
    
    Capabilities:
    - Analyze discharge documents for dietary restrictions
    - Search dietary guidelines for conditions
    - Consider medication interactions with food
    - Generate Indian-friendly meal plans
    """
    
    SYSTEM_PROMPT = """You are a certified nutritionist who helps patients maintain 
a healthy diet after hospital discharge. Your role is to:

1. Analyze the patient's medical condition from discharge documents
2. Consider dietary restrictions based on diagnosis
3. Account for medication-food interactions
4. Create practical, personalized meal plans
5. Recommend foods to avoid and foods to include

Important guidelines:
- Prioritize Indian cuisine options when not specified otherwise
- Be specific about portion sizes
- Mention timing of meals relative to medications
- Always recommend consulting a doctor/dietitian for serious conditions
- Consider cultural and practical constraints

Format meal plans clearly with times and portions."""

    def process(self, query: str) -> str:
        """
        Process a diet-related query.
        """
        # Search discharge for medical conditions
        discharge_results = self.search_discharge("diagnosis condition disease medication", k=5)
        
        # Search dietary guidelines
        diet_results = self.search_dietary(query, k=5)
        
        discharge_context = format_search_results(discharge_results) if discharge_results else "No discharge documents uploaded."
        diet_context = format_search_results(diet_results) if diet_results else "Dietary guidelines not indexed yet."
        
        prompt = f"""{self.SYSTEM_PROMPT}

## Patient's Medical Information (from discharge):
{discharge_context}

## Relevant Dietary Guidelines:
{diet_context}

## Patient's Question:
{query}

## Instructions:
Based on the medical information and dietary guidelines, provide personalized 
advice. Consider:
- The patient's diagnosis and any dietary restrictions
- Medications that may interact with foods
- Practical, easy-to-follow recommendations

Cite sources when referencing guidelines.

## Response:"""
        
        return self.ask_llm(prompt)
    
    def generate_meal_plan(self, days: int = 7) -> str:
        """Generate a personalized meal plan based on medical conditions."""
        # Get medical context
        discharge_results = self.search_discharge("diagnosis condition treatment medication diet", k=8)
        
        # Get dietary guidelines
        diet_results = self.search_dietary("meal plan diet schedule nutrition", k=5)
        
        discharge_context = format_search_results(discharge_results) if discharge_results else "No medical conditions found."
        diet_context = format_search_results(diet_results) if diet_results else ""
        
        prompt = f"""{self.SYSTEM_PROMPT}

## Patient's Medical Information:
{discharge_context}

## Dietary Guidelines:
{diet_context}

## Task:
Create a {days}-day meal plan suitable for the patient's condition. Include:

### Dietary Restrictions
- Foods to AVOID (based on condition/medications)
- Foods to INCLUDE (beneficial for recovery)

### Sample {days}-Day Meal Plan

| Day | Breakfast | Mid-Morning | Lunch | Evening Snack | Dinner |
|-----|-----------|-------------|-------|---------------|--------|
| Day 1 | ... | ... | ... | ... | ... |
| Day 2 | ... | ... | ... | ... | ... |
...

### Hydration Guidelines
- Water intake recommendations
- Beverages to avoid

### Timing Notes
- When to eat relative to medications
- Gap between meals

### Shopping List
Key ingredients to buy for this meal plan.

Focus on Indian cuisine unless otherwise specified. Be practical and affordable.

## Personalized Meal Plan:"""
        
        return self.ask_llm(prompt)
    
    def foods_to_avoid(self) -> str:
        """List foods to avoid based on medical conditions and medications."""
        discharge_results = self.search_discharge("diagnosis medication medicine drug treatment", k=8)
        diet_results = self.search_dietary("avoid restriction contraindicated", k=5)
        
        if not discharge_results:
            return """I need your medical information to provide personalized advice.

Please upload your discharge summary, and I can tell you:
- Foods to avoid based on your condition
- Foods that may interact with your medications
- Substances that could affect your recovery

General advice (without your medical details):
- Limit processed and high-sodium foods
- Avoid excessive sugar and saturated fats
- Stay hydrated with water
- Limit alcohol consumption"""
        
        discharge_context = format_search_results(discharge_results)
        diet_context = format_search_results(diet_results) if diet_results else ""
        
        prompt = f"""{self.SYSTEM_PROMPT}

## Patient's Medical Information:
{discharge_context}

## Dietary Guidelines:
{diet_context}

## Task:
Create a comprehensive list of foods and substances the patient should AVOID 
based on their medical condition and medications.

### Foods to Avoid

| Food/Substance | Reason | Severity |
|----------------|--------|----------|
| ... | (why to avoid) | High/Medium/Low |

### Medication-Food Interactions
Specific interactions to watch for with prescribed medications.

### General Precautions
Other dietary cautions for recovery.

Cite sources and recommend professional consultation for specific concerns.

## Foods to Avoid Report:"""
        
        return self.ask_llm(prompt)
