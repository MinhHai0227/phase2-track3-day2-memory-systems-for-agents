from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage

from app.config import load_settings
from app.graph import build_agent_graph
from app.memory_store import LocalMemoryStack


def records_to_messages(records: list[dict[str, str]]):
    messages = []
    for record in records:
        if record.get("role") == "assistant":
            messages.append(AIMessage(content=record.get("content", "")))
        else:
            messages.append(HumanMessage(content=record.get("content", "")))
    return messages


def messages_to_records(messages) -> list[dict[str, str]]:
    records = []
    for message in messages:
        role = "assistant" if isinstance(message, AIMessage) else "user"
        records.append({"role": role, "content": str(message.content)})
    return records


def latest_ai(messages) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return str(message.content)
    return ""


def main() -> None:
    settings = load_settings()
    if not settings.openai_api_key:
        raise RuntimeError("Missing OPENAI_API_KEY. Copy .env.example to .env and add your key.")

    memory_stack = LocalMemoryStack(
        settings.data_dir,
        short_term_window=settings.short_term_window,
    )
    graph = build_agent_graph(memory_stack=memory_stack, settings=settings)
    messages = records_to_messages(memory_stack.load_recent_chat_records())

    print("Smart Confide Memory Agent")
    print("Nhap 'exit' de thoat.")
    print("Lenh: /memory de xem memory, /forget de xoa memory user.\n")

    while True:
        user_text = input("Ban: ").strip()
        if user_text.lower() in {"exit", "quit", "q"}:
            break
        if user_text == "/memory":
            snapshot = memory_stack.memory_snapshot()
            print(json.dumps(snapshot, ensure_ascii=False, indent=2))
            continue
        if user_text == "/forget":
            memory_stack.clear_user_memory()
            messages = []
            print("Da xoa profile, episodic memory va short-term chat local.\n")
            continue
        if not user_text:
            continue

        state = graph.invoke(
            {
                "messages": [*messages, HumanMessage(content=user_text)],
                "memory_budget": settings.memory_budget,
            }
        )
        messages = state["messages"][-settings.short_term_window :]
        memory_stack.save_recent_chat_records(messages_to_records(messages))

        print(f"\nAgent: {latest_ai(messages)}\n")


if __name__ == "__main__":
    main()
