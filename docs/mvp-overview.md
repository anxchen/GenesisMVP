# Genesis MVP Backend Overview

## Pipeline Modules (🟢 Now)
- **Upload Service**: Issues presigned URLs (stubbed locally) and persists finalized media file metadata.
- **Transcription Service**: Uses `faster-whisper` to produce full transcripts + word timings and stores them in the DB/artifact tree.
- **Scene Detection**: Runs PySceneDetect, extracts preview frames, and captions them with BLIP for downstream narrative tools.
- **Chapter Grouping**: Rule-based grouping that rolls contiguous scenes into chapters and records scene-to-chapter links.
- **Assembly**: Builds a rendered MP4 by trimming each scene, concatenating via FFmpeg, and optionally mixing a narration track with ducked nat sound.
- **Orchestration**: `ProjectPipelineService` sequences the steps and records step-level telemetry in `runs.step_details`.

### Running the Pipeline Locally
- `ProjectPipelineService` now executes real ML/CV workloads (Whisper → PySceneDetect + BLIP → Chapterize → optional narration alignment → FFmpeg assemble) and persists intermediate metadata.
- CLI entry point: `PYTHONPATH=./src python -m genesis.cli.process_project --project-id <uuid>`
- Voiceover options: append `--voiceover path/to/audio.mp3 [--voiceover-offset 1.2 --voiceover-gain 1.1 --bed-gain 0.25]` to mix narration over the rough cut.
- Outputs:
  - `transcripts` table + transcript artifacts (segments + Whisper metadata)
  - `scene` table with preview `jpg`s (`output/scene_previews/`) and captions in `metadata_json`
  - Rendered MP4 artifacts in `output/renders/` (voiceover mix if provided) and managed narration WAV copies in `output/voiceovers/`

## Code Layout
- `src/genesis/api`: FastAPI app + routers for projects, uploads, runs, artifacts.
- `src/genesis/models`: SQLAlchemy ORM models aligned with PRD tables.
- `src/genesis/services`: Service layer for transcription, scene detection, captioning, chapterizing, assembly, and orchestration.
- `src/genesis/ml`: Shared ML model loaders (Whisper + BLIP pipelines).
- `src/genesis/utils`: ffmpeg helpers for trimming, frame extraction, and concatenation.
- `src/genesis/orchestration`: Step Functions hand-off placeholder.
- `migrations`: Alembic environment + initial schema migration.

## Immediate Next Steps
1. Integrate real storage targets (S3 URIs) and move artifacts out of the local workspace when running in cloud environments.
2. Add configurable model sizing + batching for Whisper and BLIP to balance quality vs. runtime.
3. Expand narration alignment with transcript-aware timing (auto offsets per chapter) and sidechain compression.
4. Persist per-scene confidence metrics and expose them through the API for editors.
5. Add unit/integration tests around the pipeline and ffmpeg utilities.
6. Bring the orchestration into Step Functions / Lambda once cloud infra is ready.
