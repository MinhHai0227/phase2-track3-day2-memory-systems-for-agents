from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_model: str
    memory_budget: int
    short_term_window: int
    temperature: float
    data_dir: Path


def load_settings() -> Settings:
    load_dotenv(ROOT_DIR / ".env")

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        memory_budget=int(os.getenv("MEMORY_BUDGET", "1800")),
        short_term_window=int(os.getenv("SHORT_TERM_WINDOW", "12")),
        temperature=float(os.getenv("TEMPERATURE", "0.4")),
        data_dir=DATA_DIR,
    )
