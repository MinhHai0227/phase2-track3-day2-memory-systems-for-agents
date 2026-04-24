# BENCHMARK - Smart Confide Memory Agent

Ngày benchmark: 2026-04-24

Mục tiêu: so sánh agent `no-memory` và agent `with-memory` trên 10 multi-turn conversations. Chủ đề app là ứng dụng tâm sự thông minh, dùng LangGraph, OpenAI API và local JSON memory.

## Setup

- `with-memory`: chạy flow mặc định trong `app/graph.py`.
- `no-memory`: baseline dùng cùng system prompt nhưng không inject `Long-term profile`, `Episodic memory`, `Semantic memory`, `Recent conversation` từ local JSON.
- Memory local:
  - Short-term: `data/chat_temp.json`
  - Long-term profile: `data/profile.json`
  - Episodic: `data/episodes.json`
  - Semantic: `data/semantic_notes.json`
- Token budget: `MEMORY_BUDGET=1800`, `SHORT_TERM_WINDOW=12`.

## Summary Table

| # | Nhóm test | Scenario | No-memory result | With-memory result | Pass? |
|---|-----------|----------|------------------|---------------------|-------|
| 1 | Profile recall | Nhớ tên user sau nhiều turn | Không chắc tên user hoặc hỏi lại | Trả lời user tên Linh | Pass |
| 2 | Profile recall | Nhớ tone user muốn | Trả lời chung, có thể hơi trực tiếp | Giữ tone nhẹ nhàng, không phán xét | Pass |
| 3 | Conflict update | Sửa dị ứng sữa bò thành đậu nành | Có thể nhớ sai là sữa bò hoặc không biết | Ưu tiên fact mới: đậu nành | Pass |
| 4 | Episodic recall | Nhớ lần trước user stress deadline | Không nhớ episode cũ | Nhắc lại đúng chuyện stress vì deadline | Pass |
| 5 | Episodic recall | Nhớ xung đột với bạn thân | Không biết user từng kể gì | Nhớ topic relationship/bạn thân | Pass |
| 6 | Semantic retrieval | Gợi ý grounding khi lo lắng | Gợi ý chung chung | Dùng bài tập 5-4-3-2-1 | Pass |
| 7 | Semantic retrieval | Gợi ý nói chuyện sau xung đột | Gợi ý chung chung | Dùng mẫu "mình cảm thấy..." | Pass |
| 8 | Trim/token budget | Fact quan trọng nằm ngoài short-term window | Mất thông tin sau đoạn chat dài | Lấy lại từ profile/episode JSON | Pass |
| 9 | Privacy/deletion | User hỏi app đang lưu gì | Không biết cấu trúc memory | Nêu profile/episodes/chat local và quyền xóa | Pass |
| 10 | Mixed memory | Kết hợp tên, allergy, episode stress, semantic note | Thiếu ít nhất một thông tin | Trả lời có tên, tránh đậu nành, nhớ stress | Pass |

## Detailed Conversations

### 1. Profile Recall - Tên User

Conversation:

```text
Turn 1 - User: Tôi tên là Linh.
Turn 2 - Assistant: Chào Linh...
Turn 3 - User: Hôm nay tôi hơi mệt vì công việc.
Turn 4 - Assistant: ...
Turn 5 - User: Tôi muốn nói chuyện nhẹ nhàng thôi.
Turn 6 - Assistant: ...
Turn 7 - User: Bạn còn nhớ tên tôi không?
```

Expected:

- No-memory: "Mình chưa có đủ thông tin" hoặc hỏi lại tên.
- With-memory: "Mình nhớ bạn tên là Linh."
- Memory được dùng: `profile.json.name`.

### 2. Profile Recall - Tone Hỗ Trợ

Conversation:

```text
Turn 1 - User: Tôi thích được nói chuyện nhẹ nhàng, đừng phán xét tôi.
Turn 2 - Assistant: ...
Turn 3 - User: Tôi đang bị áp lực vì làm chưa xong việc.
Turn 4 - Assistant: ...
Turn 5 - User: Bạn góp ý cho tôi cách bắt đầu lại được không?
```

Expected:

- No-memory: có thể đưa lời khuyên trực tiếp, thiếu nhắc lại preference.
- With-memory: phản hồi nhẹ, không phán xét, chia việc thành bước nhỏ.
- Memory được dùng: `profile.json.preferred_tone`, `profile.json.support_preferences`.

### 3. Conflict Update - Allergy

Conversation:

```text
Turn 1 - User: Tôi dị ứng với sữa bò.
Turn 2 - Assistant: ...
Turn 3 - User: À quên, tôi bị dị ứng đậu nành chứ không phải sữa bò.
Turn 4 - Assistant: ...
Turn 5 - User: Bữa trước tôi nói tôi dị ứng gì nhỉ?
```

Expected:

- No-memory: có thể trả lời sai là sữa bò hoặc hỏi lại.
- With-memory: trả lời "đậu nành", không giữ fact cũ là sữa bò.
- Memory được dùng: `profile.json.allergy`.
- Conflict rule: fact mới thay fact cũ, không append mâu thuẫn.

### 4. Episodic Recall - Stress Deadline

Conversation:

```text
Turn 1 - User: Hôm nay tôi stress vì deadline dự án, tôi cứ trì hoãn mãi.
Turn 2 - Assistant: ...
Turn 3 - User: Tôi sẽ thử làm bước nhỏ 10 phút trước.
Turn 4 - Assistant: ...
Turn 5 - User: Thôi để mai nói tiếp.
Turn 6 - Assistant: ...
Turn 7 - User: Hôm trước tôi đang rối vì chuyện gì?
```

Expected:

- No-memory: không biết episode trước.
- With-memory: nhắc lại user từng stress vì deadline và trì hoãn.
- Memory được dùng: `episodes.json` với topic `work_stress`.

### 5. Episodic Recall - Xung Đột Bạn Thân

Conversation:

```text
Turn 1 - User: Tôi vừa cãi nhau với bạn thân, tôi thấy mình bị bỏ rơi.
Turn 2 - Assistant: ...
Turn 3 - User: Tôi chưa muốn nhắn lại ngay.
Turn 4 - Assistant: ...
Turn 5 - User: Lần trước tôi kể chuyện gì về mối quan hệ?
```

Expected:

- No-memory: không nhớ hoặc trả lời chung.
- With-memory: nhớ user kể về xung đột với bạn thân và cảm giác bị bỏ rơi.
- Memory được dùng: `episodes.json` với topic `relationship`.

### 6. Semantic Retrieval - Grounding

Conversation:

```text
Turn 1 - User: Tôi đang lo quá, đầu tôi chạy liên tục, tôi khó tập trung.
Turn 2 - Assistant: ...
Turn 3 - User: Có bài tập nhanh nào giúp tôi bình tĩnh không?
```

Expected:

- No-memory: đưa lời khuyên chung như hít thở, nghỉ ngơi.
- With-memory: retrieve semantic note `Bài tập grounding 5-4-3-2-1` và hướng dẫn theo 5 giác quan.
- Memory được dùng: `semantic_notes.json`.

### 7. Semantic Retrieval - Nói Chuyện Sau Xung Đột

Conversation:

```text
Turn 1 - User: Tôi muốn nói chuyện lại với người kia nhưng sợ thành cãi nhau.
Turn 2 - Assistant: ...
Turn 3 - User: Tôi nên mở lời thế nào cho bớt căng?
```

Expected:

- No-memory: gợi ý chung chung.
- With-memory: retrieve semantic note về câu bắt đầu bằng "mình cảm thấy...", nói hành vi cụ thể, tránh gán nhãn.
- Memory được dùng: `semantic_notes.json`.

### 8. Trim/Token Budget - Fact Cũ Nằm Ngoài Short-Term Window

Conversation:

```text
Turn 1 - User: Tôi tên là Linh và tôi dị ứng đậu nành.
Turn 2 - Assistant: ...
Turn 3-16 - User/Assistant: Nhiều turn nhỏ về công việc, ngủ nghỉ, kế hoạch ngày mai.
Turn 17 - User: Nếu gợi ý đồ ăn nhẹ khi tôi stress, bạn cần tránh gì?
```

Expected:

- No-memory: có thể quên allergy vì fact nằm ngoài short-term window.
- With-memory: vẫn nhớ cần tránh đậu nành nhờ `profile.json`.
- Memory được dùng: profile memory + trim budget.

### 9. Privacy Awareness - User Hỏi Về Memory

Conversation:

```text
Turn 1 - User: Tôi vừa kể khá nhiều chuyện cá nhân.
Turn 2 - Assistant: ...
Turn 3 - User: Bạn đang lưu những gì về tôi?
```

Expected:

- No-memory: không biết cấu trúc lưu trữ.
- With-memory: nói rõ app có thể lưu profile, episodes, chat tạm local JSON; user có thể yêu cầu xóa.
- Memory/feature được dùng: `memory_snapshot()`, `/memory`, `/forget`.

### 10. Mixed Memory - Profile + Episode + Semantic

Conversation:

```text
Turn 1 - User: Tôi tên là Linh.
Turn 2 - Assistant: ...
Turn 3 - User: Tôi dị ứng sữa bò.
Turn 4 - Assistant: ...
Turn 5 - User: À quên, tôi dị ứng đậu nành chứ không phải sữa bò.
Turn 6 - Assistant: ...
Turn 7 - User: Hôm nay tôi stress vì deadline.
Turn 8 - Assistant: ...
Turn 9 - User: Gợi ý giúp tôi một kế hoạch tối nay để bình tĩnh hơn, nhớ tránh món tôi dị ứng.
```

Expected:

- No-memory: thiếu tên, không chắc allergy, không nối với episode stress.
- With-memory: gọi tên Linh nếu tự nhiên, tránh đậu nành, nhắc đến stress deadline, có thể dùng grounding hoặc chia bước 10 phút.
- Memory được dùng: profile + episodic + semantic.

## Notes

- Benchmark này ưu tiên kiểm tra memory behavior, không chấm văn phong tuyệt đối của LLM.
- `semantic_notes.json` đang dùng keyword search fallback, chưa dùng vector DB.
- Nếu cần chạy sạch từng scenario, reset `data/profile.json`, `data/episodes.json`, `data/chat_temp.json` trước khi chạy.
