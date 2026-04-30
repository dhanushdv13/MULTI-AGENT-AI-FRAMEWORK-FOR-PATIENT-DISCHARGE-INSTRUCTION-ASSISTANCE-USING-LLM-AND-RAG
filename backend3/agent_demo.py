import os
from datetime import datetime
from dotenv import load_dotenv

from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

from langchain.tools import tool
from langchain.agents import create_agent
from model import llm
# ---------------------------
# Tools
# ---------------------------
@tool
def greet_user(name: str) -> str:
    """Greets the user with their name."""
    return f"Hello {name}! 👋 Nice to meet you."

@tool
def get_time() -> str:
    """Returns the current system time."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"Current time is {now}"

tools = [greet_user, get_time]

con = sqlite3.connect("agent_memory.db", check_same_thread=False)
checkpointer = SqliteSaver(con)

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="You are a helpful assistant. Use tools when needed.",
    checkpointer=checkpointer
)

config = {"configurable": {
                "thread_id": 'demo101'
            }
}

if __name__ == "__main__":
    response = agent.invoke(
        {"messages": [input()]},
        config=config
    )

    print(response['messages'][-1].content)
