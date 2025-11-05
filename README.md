# Genesis MVP Backend

Genesis is an AI-assisted long-form video editor. This repository contains the Phase 1 backend MVP that ingests raw clips, transcribes speech, detects scenes, groups chapters, optionally mixes narration, and exports a rough-cut video—all backed by an SQLAlchemy database and exposed through service/CLI layers.

## Features

- **Upload intake** (presigned URL scaffold + database records)
- **Transcription** via `faster-whisper`
- **Scene detection** with `scenedetect`, preview frame extraction, and BLIP captions
- **Chapter grouping** (rule-based)
- **Assembly** (FFmpeg trims + concatenation, optional narration mix)
- **Orchestration** through `ProjectPipelineService`
- **SQLAlchemy ORM** models, Alembic migrations, FastAPI-ready services

## Requirements

- macOS/Linux with FFmpeg installed (`brew install ffmpeg` on macOS)
- Python **3.11** (PyTorch/SceneDetect target this version)
- Optional GPU acceleration (whisper / torch will fall back to CPU)

## Setup

```bash
git clone https://github.com/anxchen/GenesisMVP.git
cd GenesisMVP

# create Python 3.11 environment
/opt/homebrew/bin/python3.11 -m venv venv
source venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .

# run database migrations (SQLite default)
PYTHONPATH=./src alembic upgrade head
```

The project writes artifacts under `output/` by default (change via `GENESIS_ARTIFACT_ROOT`).

## Core Commands

### Run the pipeline locally

```bash
PYTHONPATH=./src python -m genesis.cli.process_project \
  --project-id <uuid> \
  [--voiceover /path/to/audio.mp3] \
  [--voiceover-offset 0.0] \
  [--voiceover-gain 1.0] \
  [--bed-gain 0.3]
```

Outputs:
- `output/scene_previews/` – JPG per scene with BLIP captions in `scene.metadata_json`
- `output/voiceovers/` – normalized WAV copy of narration (if provided)
- `output/renders/` – final stitched MP4 (voiceover mix if provided)

### Inspect pipeline state

```
PYTHONPATH=./src python scripts/print_pipeline_state.py
```
Enter the project UUID when prompted to dump runs/media/transcripts/scenes/chapters/artifacts.

## Configuration

Env vars (prefix `GENESIS_`) override defaults defined in `src/genesis/config.py`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `GENESIS_WHISPER_MODEL_SIZE` | `small` | `faster-whisper` model to use |
| `GENESIS_WHISPER_COMPUTE_TYPE` | `int8` | compute precision |
| `GENESIS_CAPTION_MODEL_NAME` | `Salesforce/blip-image-captioning-base` | BLIP model |
| `GENESIS_ARTIFACT_ROOT` | `output` | base directory for renders/previews |
| `GENESIS_FFMPEG_BINARY` | `ffmpeg` | FFmpeg binary path |
| `DATABASE_URL` | SQLite (`sqlite+aiosqlite:///./genesis.db`) | DB connection |

Set them before running the CLI, e.g.:

```bash
export GENESIS_WHISPER_MODEL_SIZE=medium
export GENESIS_ARTIFACT_ROOT=/tmp/genesis_artifacts
```

## Project Layout

- `src/genesis/api/` – FastAPI routers (projects, uploads, runs, artifacts)
- `src/genesis/models/` – SQLAlchemy ORM models (projects, media_files, transcripts, scenes, chapters, runs, artifacts)
- `src/genesis/services/` – Service layer (transcription, scene detection, chapters, assembly, narration, pipeline orchestrator)
- `src/genesis/ml/` – Shared ML model loaders for Whisper + BLIP
- `src/genesis/utils/ffmpeg.py` – FFmpeg helpers (trim, concat, frame capture, voiceover mix)
- `src/genesis/cli/process_project.py` – CLI entry for local runs
- `migrations/` – Alembic migrations
- `docs/` – Project overview and iteration notes
- `output/` – Generated artifacts (ignored by git)

## Troubleshooting

- **`ModuleNotFoundError: pydantic_settings`** – reinstall dependencies (`python -m pip install -e .`), ensure `pydantic-settings` installed.
- **Whisper/SceneDetect import errors** – confirm you’re running Python ≥3.11 and `pip install -e .` completed.
- **Torch/torchvision wheel missing** – same root cause as above; torch currently ships wheels for 3.11 on Apple Silicon.
- **FFmpeg missing** – install it (`brew install ffmpeg`) or set `GENESIS_FFMPEG_BINARY` to a custom path.
- **No render produced** – check CLI output (`step_details` in final log) or run `scripts/print_pipeline_state.py` to inspect DB state.

## Next Steps

- Integrate real storage (S3) & orchestration (Step Functions)
- Add unit/integration tests for services, ffmpeg utilities, and API
- Enhance narration alignment with transcript-aware timing and sidechain compression
- Expose pipeline control via FastAPI endpoints / AWS Lambda wrappers

---
Feel free to open issues or PRs as we continue building Genesis into a fully automated, narrative-driven video editor.
