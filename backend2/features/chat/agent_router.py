"""
AgentRouter — wraps backend2's MultiAgent for use inside FastAPI.
Uses per-vector_id caching and runs blocking invoke() in a threadpool.
"""
import traceback
from starlette.concurrency import run_in_threadpool
from langchain_core.messages import ToolMessage
from multi_agent import MultiAgent

_agent_cache: dict[str, MultiAgent] = {}


def _get_or_create_agent(vector_id: str) -> MultiAgent:
    if vector_id not in _agent_cache:
        _agent_cache[vector_id] = MultiAgent(vectorstore=vector_id)
    return _agent_cache[vector_id]


def _invoke_agent(vector_id: str, query: str) -> dict:
    try:
        agent = _get_or_create_agent(vector_id)
        result = agent.invoke(query)

        messages = result.get("messages", [])
        final_message = messages[-1] if messages else None

        agent_name = "AI Assistant"
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage) and msg.name in ("diet_specialist", "discharge_specialist"):
                agent_name = msg.name.replace("_", " ").title()
                break

        raw_content = final_message.content if hasattr(final_message, "content") else str(final_message)

        # Anthropic returns structured content blocks: [{'type': 'text', 'text': '...'}]
        # Flatten to a plain string so Pydantic's ChatResponse (response: str) validates correctly.
        if isinstance(raw_content, list):
            response_text = "\n".join(
                block.get("text", str(block))
                for block in raw_content
                if isinstance(block, dict)
            ) or str(raw_content)
        else:
            response_text = raw_content
        return {"agent": agent_name, "response": response_text}

    except Exception:
        print("\n========== AGENT ERROR TRACEBACK ==========")
        traceback.print_exc()
        print("===========================================\n")
        raise


class AgentRouter:
    async def ask(self, vector_id: str, query: str) -> dict:
        return await run_in_threadpool(_invoke_agent, vector_id, query)
