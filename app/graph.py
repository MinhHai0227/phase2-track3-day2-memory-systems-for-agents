from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from app.config import Settings, load_settings
from app.memory_store import LocalMemoryStack
from app.prompts import SYSTEM_PROMPT, build_memory_prompt


class MemoryState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    user_profile: dict[str, Any]
    episodes: list[dict[str, Any]]
    semantic_hits: list[str]
    memory_budget: int
    assistant_reply: str


def latest_user_text(messages: list[AnyMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return str(message.content)
    return ""


def latest_ai_text(messages: list[AnyMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return str(message.content)
    return ""


def recent_conversation_lines(messages: list[AnyMessage], limit: int = 8) -> list[str]:
    lines: list[str] = []
    for message in messages[-limit:]:
        role = "User" if isinstance(message, HumanMessage) else "Assistant"
        lines.append(f"{role}: {message.content}")
    return lines


def build_agent_graph(
    memory_stack: LocalMemoryStack | None = None,
    settings: Settings | None = None,
):
    settings = settings or load_settings()
    memory_stack = memory_stack or LocalMemoryStack(
        settings.data_dir,
        short_term_window=settings.short_term_window,
    )

    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=settings.temperature,
        api_key=settings.openai_api_key,
    )

    def retrieve_memory(state: MemoryState) -> dict[str, Any]:
        query = latest_user_text(state.get("messages", []))
        return memory_stack.retrieve(
            query=query,
            memory_budget=state.get("memory_budget", settings.memory_budget),
        )

    def generate_response(state: MemoryState) -> dict[str, Any]:
        messages = state.get("messages", [])
        memory_prompt = build_memory_prompt(
            user_profile=state.get("user_profile", {}),
            episodes=state.get("episodes", []),
            semantic_hits=state.get("semantic_hits", []),
            recent_conversation=recent_conversation_lines(messages),
            memory_budget=state.get("memory_budget", settings.memory_budget),
        )
        prompt_messages = [
            SystemMessage(content=f"{SYSTEM_PROMPT}\n\n{memory_prompt}"),
            *messages[-settings.short_term_window :],
        ]
        response = llm.invoke(prompt_messages)
        return {"messages": [response], "assistant_reply": str(response.content)}

    def save_memory(state: MemoryState) -> dict[str, Any]:
        user_text = latest_user_text(state.get("messages", []))
        assistant_text = state.get("assistant_reply") or latest_ai_text(
            state.get("messages", [])
        )
        if user_text and assistant_text:
            memory_stack.save_after_turn(user_text, assistant_text)
        return {}

    graph = StateGraph(MemoryState)
    graph.add_node("retrieve_memory", retrieve_memory)
    graph.add_node("generate_response", generate_response)
    graph.add_node("save_memory", save_memory)

    graph.add_edge(START, "retrieve_memory")
    graph.add_edge("retrieve_memory", "generate_response")
    graph.add_edge("generate_response", "save_memory")
    graph.add_edge("save_memory", END)

    return graph.compile()
