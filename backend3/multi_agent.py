# multi_agent.py
import sqlite3
import json
from langchain_core.messages import HumanMessage
from langchain.tools import tool
from langchain.agents import create_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from model import llm

from agent_utils.diet_agent_utils import (
    DIET_AGENT_TOOLS,
    DIET_AGENT_SYSTEM_PROMPT,
)
from agent_utils.discharge_agent_utils import (
    DISCHARGE_AGENT_TOOLS,
    DISCHARGE_AGENT_SYSTEM_PROMPT,
)
from agent_utils.bill_validator_agent_utils import (
    BILL_VALIDATOR_TOOLS,
    BILL_VALIDATOR_SYSTEM_PROMPT,
)
from agent_utils.medicine_agent_utils import (
    MEDICINE_AGENT_TOOLS,
    MEDICINE_AGENT_SYSTEM_PROMPT,
)


class MultiAgent:
    def __init__(self, vectorstore: str):
        self.vectorstore = vectorstore

        # Shared LangGraph config — used by the main agent and all subagents
        self.config = {
            "configurable": {
                "thread_id": str(self.vectorstore)
            }
        }

        # SQLite checkpointer for conversation memory
        con = sqlite3.connect("agent_memory.db", check_same_thread=False)
        self.checkpointer = SqliteSaver(con)
        self.llm = llm

        vid = self.vectorstore   # short alias for use in prompts

        # ── Discharge agent ──────────────────────────────────
        self.discharge_agent = create_agent(
            model=self.llm,
            tools=DISCHARGE_AGENT_TOOLS,
            system_prompt=(
                DISCHARGE_AGENT_SYSTEM_PROMPT +
                f"\nThe kb_name for ALL tool calls is: {vid}"
            ),
            checkpointer=self.checkpointer
        )

        # ── Diet agent ───────────────────────────────────────
        self.diet_agent = create_agent(
            model=self.llm,
            tools=DIET_AGENT_TOOLS,
            system_prompt=(
                DIET_AGENT_SYSTEM_PROMPT +
                f"\nThe kb_name for ALL tool calls is: {vid}"
            ),
            checkpointer=self.checkpointer
        )

        self.bill_validator_agent = create_agent(
            model=self.llm,
            tools=BILL_VALIDATOR_TOOLS,
            system_prompt=(
                BILL_VALIDATOR_SYSTEM_PROMPT +
                f"\nThe kb_name for ALL tool calls is: {vid}"
            ),
            checkpointer=self.checkpointer
        )

        # ── Medicine / Pharma agent ───────────────────────────
        self.medicine_agent = create_agent(
            model=self.llm,
            tools=MEDICINE_AGENT_TOOLS,
            system_prompt=MEDICINE_AGENT_SYSTEM_PROMPT,
            checkpointer=self.checkpointer
        )

        # ── Wrap sub-agents as tools for the router ──────────

        @tool("diet_specialist", description="Handles diet, nutrition, calories, food, and weight-related queries.")
        def call_diet_agent(query: str) -> str:
            print("\n-----------\nDIET SPECIALIST\n-----------")
            result = self.diet_agent.invoke({"messages": [HumanMessage(content=query)]}, config=self.config)
            with open("diet_agent_response.json", "w") as f:
                json.dump(result, f, indent=2, default=str)
            return result["messages"][-1].content

        @tool("discharge_specialist", description="Handles hospital discharge summaries, diagnoses, medications, and follow-up instructions.")
        def call_discharge_agent(query: str) -> str:
            print("\n-----------\nDISCHARGE SPECIALIST\n-----------")
            result = self.discharge_agent.invoke({"messages": [HumanMessage(content=query)]}, config=self.config)
            with open("discharge_agent_response.json", "w") as f:
                json.dump(result, f, indent=2, default=str)
            return result["messages"][-1].content

        @tool("bill_validator", description="Validates hospital bills and detects overpricing using CGHS and NPPA reference rates.")
        def call_bill_validator_agent(query: str) -> str:
            print("\n-----------\nBILL VALIDATOR\n-----------")
            result = self.bill_validator_agent.invoke({"messages": [HumanMessage(content=query)]}, config=self.config)
            with open("bill_validator_response.json", "w") as f:
                json.dump(result, f, indent=2, default=str)
            return result["messages"][-1].content

        @tool("pharma_specialist", description="Searches live retail prices of medicines in India. Use for medicine pricing, pharmacy availability, generic alternatives, and Jan Aushadhi queries.")
        def call_medicine_agent(query: str) -> str:
            print("\n-----------\nPHARMA SPECIALIST\n-----------")
            result = self.medicine_agent.invoke({"messages": [HumanMessage(content=query)]}, config=self.config)
            with open("medicine_agent_response.json", "w") as f:
                json.dump(result, f, indent=2, default=str)
            return result["messages"][-1].content

        # ── Main router agent ─────────────────────────────────

        self.multi_agent = create_agent(
            model=self.llm,
            tools=[call_diet_agent, call_discharge_agent, call_bill_validator_agent, call_medicine_agent],
            system_prompt=(
                "You are a medical router agent.\n"
                "Route queries to the correct specialist:\n"
                "- 'diet_specialist': nutrition, protein, calories, weight, food, diet plan\n"
                "- 'discharge_specialist': hospital discharge, diagnosis, medications, follow-up, procedures, medical history\n"
                "- 'bill_validator': hospital bills and detects overpricing using CGHS and NPPA reference rates\n"
                "- 'pharma_specialist': medicine prices, pharmacy availability, generic alternatives, Jan Aushadhi, drug costs\n"
                "Always route to exactly one specialist. Do not answer directly."
            ),
            checkpointer=self.checkpointer,
        )

    def invoke(self, query: str):
        return self.multi_agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config=self.config,
        )
