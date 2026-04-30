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


class MultiAgent:
    def __init__(self, vectorstore: str):
        self.vectorstore = vectorstore

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
        )

        # ── Diet agent ───────────────────────────────────────
        self.diet_agent = create_agent(
            model=self.llm,
            tools=DIET_AGENT_TOOLS,
            system_prompt=(
                DIET_AGENT_SYSTEM_PROMPT +
                f"\nThe kb_name for ALL tool calls is: {vid}"
            ),
        )

        # ── Wrap sub-agents as tools for the router ──────────

        @tool("diet_specialist", description="Handles diet, nutrition, calories, food, and weight-related queries.")
        def call_diet_agent(query: str) -> str:
            print("\n-----------\nDIET SPECIALIST\n-----------")
            result = self.diet_agent.invoke({"messages": [HumanMessage(content=query)]})
            with open("diet_agent_response.json", "w") as f:
                json.dump(result, f, indent=2, default=str)
            return result["messages"][-1].content

        @tool("discharge_specialist", description="Handles hospital discharge summaries, diagnoses, medications, and follow-up instructions.")
        def call_discharge_agent(query: str) -> str:
            print("\n-----------\nDISCHARGE SPECIALIST\n-----------")
            result = self.discharge_agent.invoke({"messages": [HumanMessage(content=query)]})
            with open("discharge_agent_response.json", "w") as f:
                json.dump(result, f, indent=2, default=str)
            return result["messages"][-1].content

        # ── Main router agent ─────────────────────────────────

        self.multi_agent = create_agent(
            model=self.llm,
            tools=[call_diet_agent, call_discharge_agent],
            system_prompt=(
                "You are a medical router agent.\n"
                "Route queries to the correct specialist:\n"
                "- 'diet_specialist': nutrition, protein, calories, weight, food, diet plan\n"
                "- 'discharge_specialist': hospital discharge, diagnosis, medications, follow-up, procedures, medical history\n"
                "Always route to exactly one specialist. Do not answer directly."
            ),
            checkpointer=self.checkpointer,
        )

    def invoke(self, query: str):
        config = {
            "configurable": {
                "thread_id": str(self.vectorstore)
            }
        }
        return self.multi_agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config=config,
        )
