from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(path, default)
        return default

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def _strip_accents(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower()


def _tokens(text: str) -> set[str]:
    normalized = _strip_accents(text)
    return {token for token in re.findall(r"[a-z0-9]+", normalized) if len(token) > 2}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_profile() -> dict[str, Any]:
    return {
        "name": None,
        "allergy": None,
        "preferred_tone": "nhe nhang, khong phan xet",
        "support_preferences": [],
        "updated_at": None,
    }


class LocalMemoryStack:
    def __init__(self, data_dir: Path, short_term_window: int = 12) -> None:
        self.data_dir = data_dir
        self.short_term_window = short_term_window
        self.profile_path = data_dir / "profile.json"
        self.episodes_path = data_dir / "episodes.json"
        self.semantic_path = data_dir / "semantic_notes.json"
        self.chat_path = data_dir / "chat_temp.json"

    def load_profile(self) -> dict[str, Any]:
        return _read_json(self.profile_path, _default_profile())

    def save_profile(self, profile: dict[str, Any]) -> None:
        profile["updated_at"] = _now_iso()
        _write_json(self.profile_path, profile)

    def load_episodes(self) -> list[dict[str, Any]]:
        return _read_json(self.episodes_path, [])

    def save_episodes(self, episodes: list[dict[str, Any]]) -> None:
        _write_json(self.episodes_path, episodes)

    def load_semantic_notes(self) -> list[dict[str, Any]]:
        return _read_json(self.semantic_path, [])

    def retrieve(self, query: str, memory_budget: int) -> dict[str, Any]:
        profile = self.load_profile()
        episodes = self.search_episodes(query, limit=3)
        semantic_hits = self.search_semantic(query, limit=3)

        return {
            "user_profile": profile,
            "episodes": episodes,
            "semantic_hits": semantic_hits,
            "memory_budget": memory_budget,
        }

    def search_episodes(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        query_tokens = _tokens(query)
        episodes = self.load_episodes()
        scored: list[tuple[int, dict[str, Any]]] = []

        for episode in episodes:
            haystack = " ".join(
                str(episode.get(key, "")) for key in ("summary", "outcome", "topic")
            )
            score = len(query_tokens & _tokens(haystack))
            if score:
                scored.append((score, episode))

        if not scored:
            return episodes[-limit:]

        return [item for _, item in sorted(scored, key=lambda pair: pair[0], reverse=True)[:limit]]

    def search_semantic(self, query: str, limit: int = 3) -> list[str]:
        query_tokens = _tokens(query)
        notes = self.load_semantic_notes()
        scored: list[tuple[int, str]] = []

        for note in notes:
            text = f"{note.get('title', '')} {note.get('content', '')}"
            score = len(query_tokens & _tokens(text))
            if score:
                scored.append((score, f"{note.get('title', '')}: {note.get('content', '')}"))

        return [
            text for _, text in sorted(scored, key=lambda pair: pair[0], reverse=True)[:limit]
        ]

    def update_profile_from_text(self, text: str) -> dict[str, Any]:
        profile = self.load_profile()
        lower_text = text.lower()
        plain_text = _strip_accents(text)

        name = self._extract_after_patterns(
            lower_text,
            plain_text,
            patterns=[
                r"(?:tên tôi là|ten toi la)\s+([^.,;!?]+)",
                r"(?:tôi tên là|toi ten la)\s+([^.,;!?]+)",
                r"(?:mình tên là|minh ten la)\s+([^.,;!?]+)",
                r"(?:gọi tôi là|goi toi la)\s+([^.,;!?]+)",
            ],
        )
        if name:
            profile["name"] = name.title()

        allergy = self._extract_allergy(lower_text, plain_text)
        if allergy:
            profile["allergy"] = allergy

        support_preferences = profile.setdefault("support_preferences", [])
        if "nhe nhang" in plain_text or "nhẹ nhàng" in lower_text:
            profile["preferred_tone"] = "nhe nhang, khong phan xet"
        if "khong phan xet" in plain_text or "không phán xét" in lower_text:
            if "khong phan xet" not in support_preferences:
                support_preferences.append("khong phan xet")

        self.save_profile(profile)
        return profile

    def _extract_after_patterns(
        self, original_lower: str, plain_text: str, patterns: list[str]
    ) -> str | None:
        for pattern in patterns:
            match = re.search(pattern, original_lower, flags=re.IGNORECASE)
            if match:
                value = self._clean_fact(match.group(1))
                return None if self._is_uncertain_fact(value) else value

            match = re.search(pattern, plain_text, flags=re.IGNORECASE)
            if match:
                value = self._clean_fact(match.group(1))
                return None if self._is_uncertain_fact(value) else value

        return None

    def _extract_allergy(self, original_lower: str, plain_text: str) -> str | None:
        patterns = [
            r"(?:tôi|toi)\s+(?:bị\s+|bi\s+)?(?:dị ứng|di ung)\s+(?:với\s+|voi\s+)?([^.,;!?]+)",
            r"(?:mình|minh)\s+(?:bị\s+|bi\s+)?(?:dị ứng|di ung)\s+(?:với\s+|voi\s+)?([^.,;!?]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, original_lower, flags=re.IGNORECASE)
            if match:
                value = self._clean_conflict_value(match.group(1))
                return None if self._is_uncertain_fact(value) else self._normalize_fact(value)

            match = re.search(pattern, plain_text, flags=re.IGNORECASE)
            if match:
                value = self._clean_conflict_value(match.group(1))
                return None if self._is_uncertain_fact(value) else self._normalize_fact(value)

        return None

    def _clean_conflict_value(self, value: str) -> str:
        value = self._clean_fact(value)
        separators = [
            " chu khong phai ",
            " chứ không phải ",
            " khong phai ",
            " không phải ",
            " instead of ",
        ]
        plain_value = _strip_accents(value)
        for separator in separators:
            plain_separator = _strip_accents(separator)
            if plain_separator in plain_value:
                index = plain_value.index(plain_separator)
                return value[:index].strip()
        return value

    def _clean_fact(self, value: str) -> str:
        return value.strip(" .,!?:;\"'").strip()

    def _is_uncertain_fact(self, value: str) -> bool:
        plain_value = _strip_accents(value)
        tokens = set(plain_value.split())
        uncertain_words = {"gi", "nhi", "vay", "nao"}
        uncertain_phrases = {"gi do", "khong nho"}
        return bool(tokens & uncertain_words) or any(
            phrase in plain_value for phrase in uncertain_phrases
        )

    def _normalize_fact(self, value: str) -> str:
        replacements = {
            "đầu nành": "đậu nành",
            "dau nanh": "đậu nành",
        }
        normalized = value.strip()
        plain_value = _strip_accents(normalized)
        return replacements.get(plain_value, normalized)

    def append_episode(self, user_text: str, assistant_text: str) -> dict[str, Any]:
        episodes = self.load_episodes()
        episode = {
            "timestamp": _now_iso(),
            "topic": self._infer_topic(user_text),
            "summary": user_text[:400],
            "outcome": assistant_text[:400],
        }
        episodes.append(episode)
        self.save_episodes(episodes[-100:])
        return episode

    def _infer_topic(self, text: str) -> str:
        plain = _strip_accents(text)
        if "cong viec" in plain or "deadline" in plain or "stress" in plain:
            return "work_stress"
        if "gia dinh" in plain:
            return "family"
        if "ban be" in plain or "nguoi yeu" in plain:
            return "relationship"
        if "di ung" in plain:
            return "profile_update"
        return "general_reflection"

    def load_recent_chat_records(self) -> list[dict[str, str]]:
        return _read_json(self.chat_path, [])

    def save_recent_chat_records(self, records: list[dict[str, str]]) -> None:
        _write_json(self.chat_path, records[-self.short_term_window :])

    def memory_snapshot(self) -> dict[str, Any]:
        return {
            "profile": self.load_profile(),
            "episodes_count": len(self.load_episodes()),
            "recent_chat_count": len(self.load_recent_chat_records()),
            "semantic_notes_count": len(self.load_semantic_notes()),
        }

    def clear_user_memory(self) -> None:
        _write_json(self.profile_path, _default_profile())
        self.save_episodes([])
        self.save_recent_chat_records([])

    def save_after_turn(self, user_text: str, assistant_text: str) -> None:
        self.update_profile_from_text(user_text)
        if self._should_store_episode(user_text):
            self.append_episode(user_text, assistant_text)

    def _should_store_episode(self, user_text: str) -> bool:
        plain = _strip_accents(user_text)
        recall_markers = {
            "bua truoc",
            "hom truoc",
            "lan truoc",
            "truoc do",
            "con nho",
            "ban nho",
            "ten toi la gi",
            "toi ten la gi",
            "cong viec hien tai",
            "hien tai cua toi",
            "toi bi di ung gi",
            "di ung gi do",
            "di ung gi thay vi",
        }
        return not any(marker in plain for marker in recall_markers)
