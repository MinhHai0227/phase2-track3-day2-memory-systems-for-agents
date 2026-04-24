# Smart Confide Memory Agent

Ung dung tam su thong minh dung LangGraph, OpenAI API va local JSON memory.

## Cau truc

```text
app/
  config.py          # Doc .env va cau hinh runtime
  graph.py           # LangGraph state, router, prompt injection, save memory
  main.py            # CLI chat demo
  memory_store.py    # 4 loai memory bang local JSON
  prompts.py         # System prompt va memory prompt
data/
  profile.json       # Long-term profile memory
  episodes.json      # Episodic memory
  semantic_notes.json# Semantic memory keyword-search fallback
BENCHMARK.md         # 10 multi-turn conversations de nop bai
REFLECTION.md        # Privacy/limitations reflection
```

## Cai dat

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Sua `.env` va dien `OPENAI_API_KEY` cua ban. Neu model mac dinh khong kha dung trong account cua ban, doi `OPENAI_MODEL`.

## Chay demo

```powershell
python -m app.main
```

Lenh trong CLI:

```text
/memory  # xem tom tat memory local hien tai
/forget  # xoa profile, episodes va chat tam cua user
exit     # thoat chuong trinh
```

Goi y test nhanh:

```text
Toi ten la Linh, toi thich duoc noi chuyen nhe nhang.
Hom nay toi rat stress vi cong viec.
Toi di ung sua bo.
A nham, toi di ung dau nanh chu khong phai sua bo.
Ban con nho toi di ung gi khong?
```

## Mapping rubric

- Short-term memory: `data/chat_temp.json`, chi luu tam cac turn gan day.
- Long-term profile: `data/profile.json`, luu fact va preference ben vung.
- Episodic memory: `data/episodes.json`, luu tom tat cac lan tam su.
- Semantic memory: `data/semantic_notes.json`, keyword search fallback.
- LangGraph: `app/graph.py` co `MemoryState`, node `retrieve_memory`, node `generate_response`, node `save_memory`.
- Benchmark: `BENCHMARK.md` co 10 multi-turn conversations so sanh `no-memory` va `with-memory`.
