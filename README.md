# Sycophancy AI Chat

## Setup

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root:
<!-- GEMINI_API_KEY=your_api_key_here -->
OPENAI_API_KEY=your_openai_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

## Run

```bash
export $(cat .env)
uvicorn main:app --reload
```

## Condition URLs

| Condition | URL | Description |
|-----------|-----|-------------|
| A | `/chat?condition=A&scenario=1` | Human × Sycophantic |
| B | `/chat?condition=B&scenario=1` | Human × Non-sycophantic |
| C | `/chat?condition=C&scenario=1` | Objective AI × Sycophantic |
| D | `/chat?condition=D&scenario=1` | Objective AI × Non-sycophantic |

 `&scenario=2` for the second scenario.

## Deployment

Deployed on Railway. Environment variables must be set in Railway dashboard under Variables tab.

uvicorn main:app --host 0.0.0.0 --port $PORT

## Qualtrics Integration

Participants are redirected from the chat interface to Qualtrics after completing 6 turns. Session ID is passed via URL parameter for data linkage: https://your-qualtrics-url?session_id=${sessionId}

Qualtrics Survey Flow includes `session_id` as embedded data set from URL.

## Data Storage

Chat session logs are stored in Supabase (`sessions` table) including:
- session_id
- condition
- scenario
- source_type
- sycophancy
- turn_count
- history (full conversation log)
- created_at

Survey response data is stored in Qualtrics and linked to chat data via `session_id`.

## SONA Integration (pending)

Random assignment endpoint `/assign` to be implemented after pilot testing. SONA URL will use: https://your-app.railway.app/assign?sona_id=%SURVEY_CODE%

