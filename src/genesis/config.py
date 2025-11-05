from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = "Genesis MVP API"
    environment: str = Field(default="development")
    aws_region: str = Field(default="us-east-1")
    s3_bucket_raw: str = Field(default="genesis-raw-media")
    s3_bucket_artifacts: str = Field(default="genesis-artifacts")
    step_function_arn: str | None = None
    whisper_model_size: str = Field(default="small")
    whisper_compute_type: str = Field(default="int8")
    caption_model_name: str = Field(default="Salesforce/blip-image-captioning-base")
    ffmpeg_binary: str = Field(default="ffmpeg")
    artifact_root: str = Field(default="output")

    class Config:
        env_prefix = "GENESIS_"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
