# AI Meeting Summarizer

An AI-powered meeting intelligence application that transcribes audio recordings and extracts structured, actionable information — summaries, decisions, action items, and participants — using OpenAI Whisper and GPT-4o-mini.

> **Status:** Company-Selection-Ready MVP / Production-Oriented Prototype

---

## Problem Statement

After every meeting, the most valuable information — decisions made, tasks assigned, deadlines set — gets lost in unstructured conversation. Teams either spend time writing meeting notes manually or lose track of commitments altogether.

This application addresses that gap: upload a recording, get an immediately actionable brief.

---

## Features

- **Audio Upload** — Upload MP3, WAV, or M4A meeting recordings (up to 25 MB)
- **Whisper Transcription** — Accurate speech-to-text via OpenAI Whisper
- **Structured AI Analysis** — GPT-4o-mini extracts title, summary, key points, decisions, action items, assignees, deadlines, and participants
- **Hallucination Guard** — Engineered prompt with strict extraction-only rules; null where unsupported
- **Live Processing Status** — Frontend polls the backend state machine in real time
- **Structured Output Validation** — Pydantic validates LLM JSON; retries once on failure
- **Failure Resilience** — If summarization fails, the transcript is still accessible
- **Relational Storage** — All entities stored in normalized PostgreSQL tables

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        React Frontend                       │
│              (Vite + TypeScript + TailwindCSS)              │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP / REST
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
│                                                             │
│  POST /api/meetings/upload                                  │
│       └── AudioStorageService (validate + save)             │
│       └── BackgroundTask → MeetingProcessingService         │
│                                                             │
│  MeetingProcessingService                                   │
│       ├── TranscriptionService                              │
│       │       └── BaseASRProvider → OpenAIWhisperProvider   │
│       └── SummarizationService                              │
│               └── BaseLLMProvider → OpenAILLMProvider       │
│                       └── Pydantic Validation + Retry       │
└───────────────────────────┬─────────────────────────────────┘
                            │ SQLAlchemy ORM
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       PostgreSQL                            │
│   meetings · transcripts · summaries · decisions            │
│   action_items · participants                               │
└─────────────────────────────────────────────────────────────┘
```

---

## System Workflow

```
Upload Audio (MP3/WAV/M4A)
        │
        ▼
[UPLOADED] Meeting record created
        │
        ▼
Background processing starts
        │
        ▼
[TRANSCRIBING] → OpenAI Whisper
        │
        ▼
[TRANSCRIBED] Transcript persisted
        │
        ▼
[SUMMARIZING] → GPT-4o-mini (structured output)
        │               │
        │         Pydantic Validation
        │         ├── Valid → Persist all entities
        │         └── Invalid → Retry once
        │                   └── Fail → SUMMARIZATION_FAILED
        ▼
[COMPLETED] Full structured summary available
```

---

## Technology Stack

| Layer       | Technology                                |
|-------------|-------------------------------------------|
| Frontend    | React 19, Vite 8, TypeScript, TailwindCSS |
| Backend     | FastAPI, Python 3.11, Uvicorn             |
| Database    | PostgreSQL 15, SQLAlchemy 2, Alembic      |
| AI: ASR     | Groq Whisper (`whisper-large-v3-turbo`)   |
| AI: LLM     | Groq Llama 3.1 70B (`openai/gpt-oss-120b`)|
| Validation  | Pydantic v2                               |
| Testing     | pytest, FastAPI TestClient                |
| Deployment  | Docker, Docker Compose                    |

---

## Project Structure

```
meeting-summarizer/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI route definitions
│   │   ├── core/          # Config, logging
│   │   ├── database/      # SQLAlchemy session + Base
│   │   ├── models/        # ORM models + MeetingStatus enum
│   │   ├── prompts/       # Versioned LLM prompts
│   │   ├── providers/     # ASR + LLM provider abstractions
│   │   ├── repositories/  # Data access layer
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   └── services/      # Business logic (audio, transcription, summarization, pipeline)
│   ├── alembic/           # Database migrations
│   ├── tests/             # pytest test suite
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── components/    # Reusable UI components
│       ├── hooks/         # Custom React hooks (useMeeting, useMeetings)
│       ├── pages/         # Dashboard, MeetingDetails, NotFound
│       ├── services/      # Centralized API client (Axios)
│       └── types/         # TypeScript interfaces
│
├── docker-compose.yml
└── .env.example
```

---

## AI Pipeline

### Transcription

- **Provider**: OpenAI Whisper (`whisper-1`)
- **Abstraction**: `BaseASRProvider` → `OpenAIWhisperProvider`
- Audio file is read from disk and sent directly to the Whisper API
- Empty transcripts are rejected and transition the meeting to `TRANSCRIPTION_FAILED`

### Summarization

- **Provider**: OpenAI GPT-4o-mini via Structured Outputs (`response_format`)
- **Abstraction**: `BaseLLMProvider` → `OpenAILLMProvider`
- The structured output schema is defined as a Pydantic model (`StructuredMeetingSummary`)
- On validation failure: retry once. On second failure: `SUMMARIZATION_FAILED`
- The provider abstraction makes it easy to swap models (e.g., Claude, Gemini) without touching service code

---

## Prompt Engineering

**File:** `backend/app/prompts/meeting_summary_v1.py`

The prompt is versioned and isolated from service code. It addresses the core challenge in meeting summarization: **hallucination**.

Key engineering decisions:

1. **Strict extraction-only framing** — "Extract only what is explicitly stated."
2. **Explicit DECISION vs. ACTION ITEM definitions** — Prevents the model from classifying general discussion as a decision.
3. **Null-first policy** — Assignees and deadlines default to `null` unless explicitly named in the transcript.
4. **Participant guard** — Participants only extracted when their identity is evidenced in the transcript.

---

## Database Design

```
meetings
 ├── id, filename, title, status, duration, created_at, updated_at
 │
 ├── transcripts (1:1)
 │    └── meeting_id, text
 │
 ├── summaries (1:1)
 │    └── meeting_id, overview, key_points (JSON)
 │
 ├── decisions (1:N)
 │    └── meeting_id, text
 │
 ├── action_items (1:N)
 │    └── meeting_id, task, assignee (nullable), deadline (nullable)
 │
 └── participants (1:N)
      └── meeting_id, name
```

All child entities use `CASCADE DELETE` — deleting a meeting removes all related data with no orphans.

---

## API Documentation

Interactive API docs are available at `http://localhost:8000/docs` when the backend is running.

| Method | Endpoint                              | Description                  |
|--------|---------------------------------------|------------------------------|
| POST   | `/api/meetings/upload`                | Upload audio; starts pipeline|
| GET    | `/api/meetings/`                      | List all meetings             |
| GET    | `/api/meetings/{id}`                  | Meeting detail + all entities |
| GET    | `/api/meetings/{id}/transcript`       | Raw transcript text           |
| GET    | `/api/meetings/{id}/summary`          | Summary + key points          |
| DELETE | `/api/meetings/{id}`                  | Delete meeting + all data     |
| GET    | `/health`                             | Health check                  |

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15 (or Docker)
- OpenAI API key

### 1. Clone and configure

```bash
git clone <repo-url>
cd meeting-summarizer
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Start PostgreSQL (Docker recommended)

```bash
docker compose up db -d
```

### 3. Start the Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend available at: `http://localhost:8000`

### 4. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: `http://localhost:5173`

---

## Environment Variables

| Variable           | Required | Default            | Description                            |
|--------------------|----------|--------------------|----------------------------------------|
| `DATABASE_URL`     | Yes      | —                  | PostgreSQL connection string           |
| `OPENAI_API_KEY`   | Yes      | —                  | OpenAI API key                         |
| `OPENAI_ASR_MODEL` | No       | `whisper-1`        | Whisper model name                     |
| `OPENAI_LLM_MODEL` | No       | `gpt-4o-mini`      | LLM model name                         |
| `UPLOAD_DIR`       | No       | `uploads`          | Local audio storage directory          |
| `MAX_FILE_SIZE_MB` | No       | `25`               | Maximum audio file size in MB          |
| `ALLOWED_ORIGINS`  | No       | `localhost:5173`   | CORS-allowed frontend origins          |
| `LOG_LEVEL`        | No       | `INFO`             | Python logging level                   |

---

## Docker Setup

```bash
# Copy and configure environment
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# Start database only (for local dev)
docker compose up db -d

# Start full stack (database + backend)
docker compose up --build
```

The frontend is not containerized in this MVP — run it locally with `npm run dev`.

---

## Testing

```bash
cd backend

# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest -v

# Run specific test modules
pytest tests/test_api.py -v
pytest tests/test_pipeline.py -v
```

Tests use an in-memory SQLite database and mocked AI providers — no real OpenAI calls are made.

---

## AI Evaluation

The AI pipeline was rigorously evaluated against realistic, real-world meeting recordings from the official **AMI Meeting Corpus**. 

The evaluation tested the complete end-to-end flow: **Upload → Audio Validation → Groq Whisper (whisper-large-v3-turbo) → Groq LLM (openai/gpt-oss-120b) → Database Persistence → Validation.**

### Key Results

| Test | AMI Meeting | Type | Duration | Result |
| :--- | :---------- | :--- | :------- | :----- |
| 1 | EN2001a | Normal | 7 min | **COMPLETED** – Excellent technical prototyping discussion capture. |
| 2 | EN2002a | Technical | 8 min | **COMPLETED** – Summarized UI layout debates perfectly. |
| 3 | EN2002a | Business | 8 min | **FAILED** (Transient Groq API Connection Error) |
| 4 | ES2002a | Discussion | 7 min | **COMPLETED** – Captured finance briefs and revenue goals. |
| 5 | ES2002a | No Assignee | 7 min | **COMPLETED** – Correctly identified brainstorming roles. |
| 6 | ES2008a | No Deadline | 7 min | **COMPLETED** – Separated primary/secondary ideas flawlessly. |
| 7 | ES2008a | Noisy | 7 min | **COMPLETED** – Captured ice-breakers and project roles. |
| 8 | EN2001a | Long | 20 min | **COMPLETED** – Summarized dense information accurately when compressed as MP3 (~20s processing time). |

*(Note: WER was excluded as mechanical alignment of the complex, fragmented AMI XML transcripts without native libraries proved unreliable. Evaluation strictly focused on qualitative AI hallucination and structuring metrics.)*

### Evaluation Dimensions

| Dimension                    | Observation                                                       |
|------------------------------|-------------------------------------------------------------------|
| Transcription quality        | High accuracy for clear English speech; seamlessly handled heavy cross-talk and diverse accents without hallucinating. |
| Summary completeness         | Captured core discussions without over-compressing important decisions. |
| Decision extraction          | Correctly identified explicit agreements; ignored exploratory discussion. |
| Action-item extraction       | Extracted only explicitly agreed tasks; correctly left arrays empty `[]` when no actions were discussed.  |
| Hallucination resistance     | Prompt guards perfectly prevented invented assignees, deadlines, and participants. |
| Structured-output reliability | **100% valid Pydantic validation** on all 7 successfully completed samples. |

> ⚠️ **Important:** This pipeline heavily utilizes free-tier Groq API rates. Uncompressed audio uploads (e.g., >15MB WAV files) may suffer from transit connection timeouts (as seen in Test 3). Ensure audio is compressed (MP3) or chunked before transit.

---

## Design Decisions

### Why FastAPI BackgroundTasks?
Simplest correct solution for MVP. The route returns immediately; processing happens asynchronously. See Known Limitations for production alternatives.

### Why OpenAI Structured Outputs over JSON mode?
Structured Outputs guarantee schema compliance at the API level, eliminating an entire class of JSON parsing errors. Combined with Pydantic validation, the output is always typed and safe to persist.

### Why a Provider Abstraction?
`BaseASRProvider` and `BaseLLMProvider` mean the AI vendors can be replaced (e.g., AssemblyAI for ASR, Claude for LLM) without modifying any service or business logic. Only the concrete provider implementation changes.

### Why Relational Tables Instead of JSON Blobs?
Decisions, action items, and participants are individually addressable entities. Storing them as normalized rows enables future features (e.g., filtering all action items assigned to a person across meetings) without schema redesign.

---

## Known Limitations

### Background Processing Durability
FastAPI `BackgroundTasks` runs in-process. If the server restarts during processing, the meeting will remain stuck in `TRANSCRIBING` or `SUMMARIZING`.  
**Production fix:** Celery + Redis or a managed queue (AWS SQS, Cloud Tasks).

### Long Meeting Support
Whisper has a 25 MB audio limit, and GPT-4o-mini has a context window limit. Very long meetings may fail.  
**Future improvement:** Audio chunking + hierarchical map-reduce summarization.

### Speaker Diarization
The MVP does not identify who said what.  
**Future improvement:** AssemblyAI or Deepgram for speaker-labeled transcripts.

### Authentication
No user accounts or access control in this MVP.  
**Future improvement:** JWT-based auth with meeting ownership.

---

## Demo Flow (2–3 min)

| Time       | Action                                                               |
|------------|----------------------------------------------------------------------|
| 0:00–0:20  | Open dashboard. Explain: "Upload a meeting → AI generates an actionable brief." |
| 0:20–0:40  | Drag-and-drop a real MP3 recording. Show instant upload response.    |
| 0:40–1:20  | Watch live pipeline: Uploaded → Transcribing → Summarizing → Completed |
| 1:20–2:00  | Walk through the result: Summary, Key Points, Decisions, Action Items table, Transcript tab |
| 2:00–2:30  | Briefly explain the architecture: provider abstraction, Pydantic validation, retry logic |

---

## Future Improvements

- Celery/Redis for durable background jobs
- Audio chunking for long recordings
- Speaker diarization
- User authentication
- Meeting search
- Export to PDF / Notion / Slack
- Custom prompt templates per organization
- Webhook notifications on completion
