from __future__ import annotations

from functools import lru_cache

from faster_whisper import WhisperModel

from genesis.config import get_settings


@lru_cache
def get_whisper_model() -> WhisperModel:
    settings = get_settings()
    return WhisperModel(
        settings.whisper_model_size,
        device="auto",
        compute_type=settings.whisper_compute_type,
    )
