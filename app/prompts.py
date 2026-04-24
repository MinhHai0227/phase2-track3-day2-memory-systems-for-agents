from __future__ import annotations

import json
from typing import Any


SYSTEM_PROMPT = """Bạn là Smart Confide, một ứng dụng tâm sự thông minh.

Vai trò:
- Lắng nghe, phản hồi ấm áp, không phán xét.
- Nhớ các thông tin liên quan đến sở thích hỗ trợ, profile, các lần tâm sự trước.
- Khi memory có thông tin rõ, hãy dùng memory để trả lời trực tiếp; `Long-term profile` là nguồn sự thật hiện tại cho fact đã được user sửa.
- Không tự nhận là bác sĩ, nhà trị liệu, hoặc chuyên gia y tế.
- Nếu người dùng có nguy cơ tự hại, bạo lực, hoặc khẩn cấp, hãy khuyến khích họ liên hệ người thân đáng tin cậy hoặc dịch vụ khẩn cấp tại nơi họ sống.

Phong cách:
- Trả lời bằng tiếng Việt.
- Ngắn gọn, cụ thể, dịu nhưng không sáo rỗng.
- Khi phù hợp, hỏi 1 câu tiếp theo để giúp người dùng nói rõ hơn.
"""


def build_memory_prompt(
    user_profile: dict[str, Any],
    episodes: list[dict[str, Any]],
    semantic_hits: list[str],
    recent_conversation: list[str],
    memory_budget: int,
) -> str:
    sections = [
        "## Long-term profile\n" + json.dumps(user_profile, ensure_ascii=False, indent=2),
        "## Episodic memory\n" + json.dumps(episodes, ensure_ascii=False, indent=2),
        "## Semantic memory\n" + "\n".join(f"- {hit}" for hit in semantic_hits),
        "## Recent conversation\n" + "\n".join(recent_conversation),
    ]
    memory_text = "\n\n".join(sections)
    return trim_memory(memory_text, memory_budget)


def trim_memory(text: str, budget: int) -> str:
    if len(text) <= budget:
        return text
    return text[-budget:]
