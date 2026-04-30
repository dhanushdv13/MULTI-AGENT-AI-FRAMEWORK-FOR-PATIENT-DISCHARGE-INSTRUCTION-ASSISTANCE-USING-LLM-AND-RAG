from typing import TypedDict, List
import os
import sqlite3
from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.agents import create_agent
from dotenv import load_dotenv

load_dotenv()

# -----------------------------
# 1. Define Custom State
# -----------------------------

class AgentState(TypedDict):
    messages: List[BaseMessage]
    user_name: str


# -----------------------------
# 2. Create LLM
# -----------------------------

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",google_api_key=os.getenv("GOOGLE_API_KEY"), temperature=0)


# -----------------------------
# 3. Create Checkpointer
# -----------------------------

con = sqlite3.connect("agent_memory.db", check_same_thread=False)

checkpointer = SqliteSaver(con)


# -----------------------------
# 4. Create Agent
# -----------------------------

agent = create_agent(
    model=llm,
    tools=[],
    state_schema=AgentState,
    system_prompt=(
        "You are a helpful assistant.\n"
        "The user's name is {user_name}. "
        "Always address them by their name."
    ),
    checkpointer=checkpointer,
)


# -----------------------------
# 5. Invoke Agent
# -----------------------------

response = agent.invoke(
    {
        "messages": [
            {"role": "user", "content": "What is my name?"}
        ],
        "user_name": "Abhijith"
    },
    config={
        "configurable": {
            "thread_id": "user-1"   # Required for SqliteSaver
        }
    }
)

print(response["messages"][-1].content)
