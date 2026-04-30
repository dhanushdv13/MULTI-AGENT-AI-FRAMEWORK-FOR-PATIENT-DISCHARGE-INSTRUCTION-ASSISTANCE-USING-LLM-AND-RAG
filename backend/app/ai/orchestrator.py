"""
AI Orchestrator - Routes queries to specialized agents (VectorID Scoped).
"""
import logging
from enum import Enum
from typing import Dict, Any, Optional

from app.ai.agents.discharge_agent import DischargeSummaryAgent
from app.ai.agents.diet_agent import DietPlanningAgent
from app.ai.agents.base import get_llm

logger = logging.getLogger("orchestrator")


class AgentType(str, Enum):
    DISCHARGE = "Discharge Summary Agent"
    BILL = "Bill Validator Agent"
    MEDICINE = "Medicine Price Comparison Agent"
    DIET = "Diet & Nutrition Agent"


class Orchestrator:
    """
    Supervisor that analyzes the query and routes it to the appropriate agent.
    """
    
    def __init__(self, vector_id: str):
        self.vector_id = vector_id
        self.llm = get_llm(temperature=0.0)  # Low temp for classification
        
        # Initialize agents
        self.agents = {
            AgentType.DISCHARGE: DischargeSummaryAgent(vector_id),
            AgentType.DIET: DietPlanningAgent(vector_id),
        }
    
    async def _classify_query(self, query: str) -> AgentType:
        """
        Classify the user query to determine the best agent.
        """
        prompt = f"""You are a query router. Your job is to select the best agent to handle a user's question.

Available Agents:
1. {AgentType.DIET.value}: For questions about food, diet plans, nutrition, what to eat/avoid, or lifestyle changes.
2. {AgentType.DISCHARGE.value}: For everything else. Questions about diagnosis, treatment, reports, follow-up, discharge summary details, or general medical questions.

User Query: "{query}"

Instructions:
- Return ONLY the exact name of the agent from the list above.
- Do not add any explanation or punctuation.

Agent Name:"""
        
        response = await self.llm.ainvoke(prompt)
        selection = response.content.strip()
        
        # Validate selection
        try:
            return AgentType(selection)
        except ValueError:
            # Fallback heuristics
            query_lower = query.lower()
            if any(k in query_lower for k in ["diet", "food", "eat", "meal", "nutrition"]):
                return AgentType.DIET
            return AgentType.DISCHARGE

    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process the user query: Classify -> Delegate -> Return Response.
        """
        # 1. Classify
        agent_type = await self._classify_query(query)
        logger.info(f"Routed query '{query}' to {agent_type}")
        
        # 2. Get Agent
        agent = self.agents[agent_type]
        
        # 3. Process
        try:
            # Check if agent has async process method, otherwise run sync in threadpool?
            # For now, we assume we will refactor agents to be async too.
            if hasattr(agent, 'process_async'):
                response = await agent.process_async(query)
            elif hasattr(agent, 'process'):
                # Temporary fallout if agent not yet updated
                # response = agent.process(query)
                # But better to assume we update them. 
                # Let's call process_async and ensure we update agents next.
                 response = await agent.process_async(query)
        except Exception as e:
            logger.error(f"Error in {agent_type}: {e}")
            response = f"I encountered an error while processing your request: {str(e)}"
            
        return {
            "query": query,
            "agent": agent_type.value,
            "response": response
        }
