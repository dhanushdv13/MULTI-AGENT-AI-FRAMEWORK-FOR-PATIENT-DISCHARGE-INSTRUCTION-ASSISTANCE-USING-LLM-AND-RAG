"""
Orchestrator - Multi-Agent Supervisor using LangChain tool-calling pattern.
All heavy imports are lazy — server starts instantly.
"""
import logging
from typing import Tuple, Optional, Dict, Any, List
from enum import Enum

from app.config import settings

logger = logging.getLogger("orchestrator")


class AgentType(str, Enum):
    """Types of specialized agents."""
    DISCHARGE = "discharge"
    BILL = "bill"
    MEDICINE = "medicine"
    DIET = "diet"
    GENERAL = "general"


SYSTEM_PROMPT = """You are a helpful healthcare assistant supervising specialized agents.

Your role is to:
1. Understand the patient's question
2. Route to the appropriate specialized agent(s)
3. Invoke multiple agents in parallel if needed
4. Synthesize results into a clear, unified response

Available Specialized Agents:
- **discharge_summary_tool**: Explains discharge documents, diagnoses, treatments
- **bill_validator_tool**: Checks bills for overcharging, validates against regulations
- **medicine_price_comparison_tool**: Finds best prices across online pharmacies
- **diet_planning_tool**: Creates meal plans based on medical conditions

Guidelines:
- For complex queries, break them down and invoke multiple agents
- Always provide helpful, empathetic responses
- If a query doesn't fit any agent, provide general healthcare guidance
- Aggregate information from multiple agents when relevant
- Maintain patient-friendly language

When uncertain which agent to use, start with the most relevant one."""


class Orchestrator:
    """
    Central orchestrator that routes queries to specialized agents.

    Uses LLM tool-calling: the LLM decides which agent(s) to invoke based on
    the user's query, then the results are returned.
    """

    def __init__(self, user_id: int):
        self.user_id = user_id

        # Lazy imports — only when user actually chats
        from app.agents.base import get_llm
        from app.agents.discharge_agent import DischargeSummaryAgent
        from app.agents.bill_agent import BillValidatorAgent
        from app.agents.medicine_agent import MedicinePriceAgent
        from app.agents.diet_agent import DietPlanningAgent

        self.llm = get_llm(temperature=0.3)

        # Initialize specialized agents
        self._discharge_agent = DischargeSummaryAgent(user_id)
        self._bill_agent = BillValidatorAgent(user_id)
        self._medicine_agent = MedicinePriceAgent(user_id)
        self._diet_agent = DietPlanningAgent(user_id)

        # Wrap agents as tools
        self.tools = self._create_agent_tools()

        # Create supervisor: LLM + bound tools
        self.supervisor = self._create_supervisor()

    # ── Intent detection (keyword-based, fast) ──────────────────────

    def detect_intent(self, query: str) -> Tuple[AgentType, float]:
        """
        Detect the primary intent from a user query using keyword scoring.
        Returns (AgentType, confidence).
        """
        q = query.lower()

        scores = {
            AgentType.DISCHARGE: 0,
            AgentType.BILL: 0,
            AgentType.MEDICINE: 0,
            AgentType.DIET: 0,
        }

        discharge_kw = [
            "discharge", "summary", "diagnosis", "explain", "condition",
            "treatment", "procedure", "doctor", "hospital", "medical",
            "medication", "prescribed", "lab", "follow-up", "report",
        ]
        bill_kw = [
            "bill", "overcharge", "cost", "price", "validate", "check bill",
            "nppa", "cghs", "expensive", "charged", "amount", "invoice",
            "insurance", "claim",
        ]
        medicine_kw = [
            "medicine price", "cheapest", "pharmacy", "compare", "1mg",
            "apollo", "pharmeasy", "where to buy", "generic", "buy medicine",
        ]
        diet_kw = [
            "diet", "food", "eat", "meal", "nutrition", "avoid eating",
            "breakfast", "lunch", "dinner", "recipe", "meal plan",
        ]

        for kw in discharge_kw:
            if kw in q:
                scores[AgentType.DISCHARGE] += 1
        for kw in bill_kw:
            if kw in q:
                scores[AgentType.BILL] += 1
        for kw in medicine_kw:
            if kw in q:
                scores[AgentType.MEDICINE] += 1
        for kw in diet_kw:
            if kw in q:
                scores[AgentType.DIET] += 1

        max_score = max(scores.values())
        if max_score == 0:
            return AgentType.GENERAL, 0.0

        best = max(scores, key=scores.get)
        total = sum(scores.values()) or 1
        confidence = max_score / total
        return best, round(confidence, 2)

    # ── Tool creation ───────────────────────────────────────────────

    def _create_agent_tools(self):
        """Wrap each specialized agent as a LangChain tool."""
        from langchain.tools import tool

        @tool
        def discharge_summary_tool(request: str) -> str:
            """Analyze discharge summaries and explain medical information.
            Use this when the user asks about diagnosis, treatment, medications,
            follow-up instructions, or anything related to their hospital stay."""
            logger.info("[Agent] discharge_summary_tool called: %s", request[:80])
            return self._discharge_agent.process(request)

        @tool
        def bill_validator_tool(request: str) -> str:
            """Validate hospital bills against regulations and detect overcharging.
            Use this when the user asks about bill amounts, overcharging, NPPA/CGHS
            rates, insurance limits, or bill breakdowns."""
            logger.info("[Agent] bill_validator_tool called: %s", request[:80])
            return self._bill_agent.process(request)

        @tool
        def medicine_price_comparison_tool(request: str) -> str:
            """Compare medicine prices across online pharmacies (1mg, Apollo, PharmEasy).
            Use this when the user asks about medicine prices, where to buy, cheapest
            options, or wants to compare prices for their prescribed medicines."""
            logger.info("[Agent] medicine_price_comparison_tool called: %s", request[:80])
            return self._medicine_agent.process(request)

        @tool
        def diet_planning_tool(request: str) -> str:
            """Create personalized diet plans based on medical conditions.
            Use this when the user asks about diet, food, meal plans, nutrition,
            foods to avoid, or dietary recommendations for their condition."""
            logger.info("[Agent] diet_planning_tool called: %s", request[:80])
            return self._diet_agent.process(request)

        return [
            discharge_summary_tool,
            bill_validator_tool,
            medicine_price_comparison_tool,
            diet_planning_tool,
        ]

    # ── Supervisor creation ─────────────────────────────────────────

    def _create_supervisor(self):
        """Create the supervisor LLM with bound tools."""
        try:
            llm_with_tools = self.llm.bind_tools(self.tools)
            return llm_with_tools
        except Exception as e:
            logger.warning("Could not bind tools to LLM: %s", e)
            return self.llm

    # ── Query processing ────────────────────────────────────────────

    def process_query(self, query: str) -> str:
        """
        Process a user query by routing to appropriate agent(s).
        The system prompt + query are sent to the LLM with tools bound.
        """
        logger.info("="*60)
        logger.info("[Chat] User query: %s", query[:200])
        logger.info("="*60)

        try:
            if self.supervisor:
                from langchain_core.messages import HumanMessage, SystemMessage

                messages = [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=query),
                ]
                response = self.supervisor.invoke(messages)

                # Check if model wants to use tools
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    tool_results = []
                    for tool_call in response.tool_calls:
                        tool_name = tool_call['name']
                        tool_args = tool_call.get('args', {})
                        logger.info("[Orchestrator] Calling tool: %s", tool_name)

                        for t in self.tools:
                            if t.name == tool_name:
                                result = t.invoke(tool_args)
                                tool_results.append(f"**{tool_name} result:**\n{result}")
                                break

                    final = "\n\n---\n\n".join(tool_results) if len(tool_results) > 1 else (tool_results[0] if tool_results else "No results.")
                    logger.info("[Orchestrator] Response length: %d chars", len(final))
                    return final

                # No tool calls — direct response
                if hasattr(response, 'content'):
                    if isinstance(response.content, list):
                        text_parts = [
                            block.get('text', '')
                            for block in response.content
                            if isinstance(block, dict) and block.get('type') == 'text'
                        ]
                        return '\n'.join(text_parts) if text_parts else str(response.content)
                    return response.content
                return str(response)
            else:
                return self._fallback_routing(query)

        except Exception as e:
            logger.error("Error in orchestrator: %s", e, exc_info=True)
            return self._fallback_routing(query)

    def _fallback_routing(self, query: str) -> str:
        """Fallback manual routing when tool-calling fails."""
        intent, _ = self.detect_intent(query)
        logger.info("[Fallback] Routing to %s", intent.value)

        if intent == AgentType.DISCHARGE:
            return self._discharge_agent.process(query)
        elif intent == AgentType.BILL:
            return self._bill_agent.process(query)
        elif intent == AgentType.MEDICINE:
            return self._medicine_agent.process(query)
        elif intent == AgentType.DIET:
            return self._diet_agent.process(query)
        else:
            return self._handle_general(query)

    def _handle_general(self, query: str) -> str:
        """Handle general queries that don't fit specific agents."""
        prompt = f"""You are a helpful healthcare assistant. The user has a general question.

Available features:
1. **Discharge Summary**: Upload discharge PDF for explanations of diagnoses, treatments, medications
2. **Bill Validation**: Upload hospital bill to check for overcharging
3. **Medicine Prices**: Compare prices across online pharmacies
4. **Diet Planning**: Get personalized meal plans

Question: {query}

Provide a helpful response and suggest which feature might help them."""
        response = self.llm.invoke(prompt)
        return response.content

    def get_agent(self, agent_type: AgentType):
        """Get a specific agent for direct access."""
        agents = {
            AgentType.DISCHARGE: self._discharge_agent,
            AgentType.BILL: self._bill_agent,
            AgentType.MEDICINE: self._medicine_agent,
            AgentType.DIET: self._diet_agent,
        }
        return agents.get(agent_type)
