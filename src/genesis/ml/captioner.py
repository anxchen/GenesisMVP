from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from transformers import pipeline

from genesis.config import get_settings


@lru_cache
def _load_captioner():
    settings = get_settings()
    return pipeline("image-to-text", model=settings.caption_model_name)


def get_captioner():
    """Return a shared Hugging Face captioning pipeline."""

    return _load_captioner()


def caption_image(image_path: str | Path, max_new_tokens: int = 60) -> str:
    pipe = get_captioner()
    result = pipe(str(image_path), max_new_tokens=max_new_tokens)
    if not result:
        return ""
    return result[0]["generated_text"].strip()
